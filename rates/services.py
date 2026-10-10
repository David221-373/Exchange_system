import logging
import os
from decimal import Decimal

import requests
from django.core.cache import cache
from django.utils import timezone

from rates.models import DirectionType, ExchangeRate, ExchangeRateHistory

logger = logging.getLogger(__name__)


def save_rate_history(rate: ExchangeRate, source: str = "manual") -> None:
    ExchangeRateHistory.objects.create(
        rate=rate,
        buy_rate=rate.buy_rate,
        sell_rate=rate.sell_rate,
        source=source,
    )


COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


def _coingecko_headers() -> dict:
    api_key = os.getenv("COINGECKO_API_KEY") or os.getenv("API_KEY") or ""
    if not api_key:
        return {}
    # CoinGecko demo keys usually start with CG-; use demo header by default.
    if api_key.startswith("CG-"):
        return {"x-cg-demo-api-key": api_key}
    return {"x-cg-pro-api-key": api_key}


def _currency_to_coingecko_id(code: str) -> str | None:
    code = code.upper()
    if code == "BTC":
        return "bitcoin"
    if code == "ETH":
        return "ethereum"
    if code in {"USDT", "TETHER"}:
        return "tether"
    return None


def _currency_to_vs(code: str) -> str | None:
    code = code.upper()
    if code in {"USD", "USD_CASH"}:
        return "usd"
    if code in {"RUB", "RUB_CASH"}:
        return "rub"
    if code == "BTC":
        return "btc"
    if code in {"USDT", "TETHER"}:
        # CoinGecko vs_currencies doesn't guarantee USDT; for USDT pairs use USD as proxy.
        return "usd"
    if code == "ETH":
        return "eth"
    return None


def _round_2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _quantize_8(value: Decimal) -> Decimal:
    """Rates like crypto per fiat need more precision than 2 decimals."""
    return value.quantize(Decimal("0.00000001"))


_CRYPTO_CODE_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "TETHER": "tether",
}


def _rate_coingecko_coin_and_vs(rate: ExchangeRate) -> tuple[str | None, str | None]:
    """
    CoinGecko simple/price returns quote per 1 base coin (e.g. rub per bitcoin).

    For cash_to_crypto (RUB -> BTC) we need the same quote asset (bitcoin) vs fiat (rub),
    then invert to crypto-per-fiat when writing buy/sell.
    """
    if rate.direction_type == DirectionType.CASH_TO_CRYPTO:
        coin_id = _currency_to_coingecko_id(rate.quote_currency.code)
        vs = _currency_to_vs(rate.base_currency.code)
        return coin_id, vs
    coin_id = _currency_to_coingecko_id(rate.base_currency.code)
    vs = _currency_to_vs(rate.quote_currency.code)
    return coin_id, vs


def _decimal_price(prices: dict, coin_id: str, vs: str) -> Decimal:
    return Decimal(str((prices.get(coin_id) or {}).get(vs) or "0"))


def market_mid_for_rate(rate: ExchangeRate, prices: dict) -> Decimal:
    """
    Mid price as quote-per-base (matches calculator: receive = send * sell_rate).

    CoinGecko often omits cross pairs like tether vs btc; USDT→BTC/ETH then uses USD bridge.
    """
    coin_id, vs = _rate_coingecko_coin_and_vs(rate)
    if coin_id and vs:
        m = _decimal_price(prices, coin_id, vs)
        if m > 0:
            return m

    if rate.direction_type != DirectionType.CRYPTO_TO_CRYPTO:
        return Decimal("0")

    base_c = rate.base_currency.code.upper()
    quote_c = rate.quote_currency.code.upper()

    # USDT -> BTC/ETH: quote per 1 USDT ≈ crypto_usd / tether_usd
    if base_c in {"USDT", "TETHER"}:
        qid = _CRYPTO_CODE_TO_COINGECKO_ID.get(quote_c)
        if qid:
            tether_usd = _decimal_price(prices, "tether", "usd")
            crypto_usd = _decimal_price(prices, qid, "usd")
            if tether_usd > 0 and crypto_usd > 0:
                return tether_usd / crypto_usd

    return Decimal("0")


def fetch_market_prices_for_active_rates() -> dict:
    """
    Fetch market prices from CoinGecko for all active ExchangeRate rows.
    Uses server-side cache (5 minutes) to respect demo API limits.
    """
    cache_key = "coingecko:simple_price:v1"
    cached = cache.get(cache_key)
    if cached:
        return cached

    coin_ids: set[str] = set()
    vs_set: set[str] = set()
    active_rates = ExchangeRate.objects.filter(is_active=True).select_related("base_currency", "quote_currency")
    for rate in active_rates:
        coin_id, vs = _rate_coingecko_coin_and_vs(rate)
        if coin_id and vs:
            coin_ids.add(coin_id)
            vs_set.add(vs)

    if any(
        r.direction_type == DirectionType.CRYPTO_TO_CRYPTO
        and r.base_currency.code.upper() in {"USDT", "TETHER"}
        for r in active_rates
    ):
        vs_set.add("usd")
        coin_ids.update({"tether", "bitcoin", "ethereum"})

    if not coin_ids or not vs_set:
        payload = {"prices": {}, "fetched_at": timezone.now().isoformat()}
        cache.set(cache_key, payload, timeout=300)
        return payload

    response = requests.get(
        COINGECKO_SIMPLE_PRICE_URL,
        params={
            "ids": ",".join(sorted(coin_ids)),
            "vs_currencies": ",".join(sorted(vs_set)),
        },
        headers=_coingecko_headers(),
        timeout=10,
    )
    response.raise_for_status()
    prices = response.json()
    payload = {"prices": prices, "fetched_at": timezone.now().isoformat()}
    cache.set(cache_key, payload, timeout=300)
    return payload


def refresh_all_active_rates(min_interval_seconds: int = 300) -> int:
    """
    Refresh all active rates from CoinGecko not more often than min_interval_seconds.
    If API fails, keep previous DB values (UI treats rates as stale based on updated_at age).
    """
    cache_key = "rates:last_refresh_ts"
    last_ts = cache.get(cache_key)
    now_ts = timezone.now().timestamp()
    if last_ts and (now_ts - float(last_ts)) < min_interval_seconds:
        return 0

    # set guard first to avoid stampede
    cache.set(cache_key, str(now_ts), timeout=min_interval_seconds)

    try:
        market_payload = fetch_market_prices_for_active_rates()
        prices = market_payload.get("prices") or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("CoinGecko refresh failed: %s", exc)
        return 0

    updated = 0
    active_rates = ExchangeRate.objects.filter(is_active=True).select_related("base_currency", "quote_currency")
    for rate in active_rates:
        coin_id, vs = _rate_coingecko_coin_and_vs(rate)
        if not coin_id or not vs:
            continue
        market = market_mid_for_rate(rate, prices)
        if market <= 0:
            continue

        margin = Decimal(str(rate.margin))
        if rate.direction_type == DirectionType.CASH_TO_CRYPTO:
            # market = fiat per 1 crypto; DB stores crypto per 1 fiat for calculator (receive = send * sell)
            inv = Decimal("1") / market
            buy = _quantize_8(inv * (Decimal("1") + margin))
            sell = _quantize_8(inv * (Decimal("1") - margin))
        elif rate.direction_type == DirectionType.CRYPTO_TO_CRYPTO:
            # USDT→BTC etc.: quote-per-base can be 1e-5; 2-decimal rounding zeros it out
            buy = _quantize_8(market * (Decimal("1") + margin))
            sell = _quantize_8(market * (Decimal("1") - margin))
        else:
            buy = _round_2(market * (Decimal("1") + margin))
            sell = _round_2(market * (Decimal("1") - margin))

        rate.buy_rate = buy
        rate.sell_rate = sell
        rate.source = "coingecko"
        rate.save(update_fields=["buy_rate", "sell_rate", "source", "updated_at"])
        save_rate_history(rate, source="coingecko")
        updated += 1

    return updated

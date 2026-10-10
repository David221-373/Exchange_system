from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render

# Пометка «устарел», если курс не перезаписывался дольше этого интервала.
RATE_STALE_MINUTES = 10

DEFAULT_MARQUEE_PAIRS = (
    ("USD", "BTC"),
    ("RUB", "BTC"),
    ("USDT", "BTC"),
    ("ETH", "BTC"),
    ("USD", "ETH"),
    ("RUB", "ETH"),
    ("USDT", "ETH"),
    ("BTC", "ETH"),
    ("USD", "USDT"),
    ("RUB", "USDT"),
    ("ETH", "USDT"),
    ("BTC", "USDT"),
    ("USDT", "RUB"),
    ("ETH", "RUB"),
    ("BTC", "RUB"),
    ("USDT", "USD"),
    ("ETH", "USD"),
    ("BTC", "USD"),
)

from core.models import City, LegalPage
from news.models import NewsItem
from orders.forms import HomeExchangeForm
from orders.models import ExchangeOrder
from rates.models import ExchangeRate, ExchangeRateHistory
from rates.services import refresh_all_active_rates
from reviews.forms import ReviewForm
from reviews.models import Review
from users.forms import CustomUserCreationForm
from users.models import UserRole


def home_page(request):
    refresh_all_active_rates(min_interval_seconds=300)
    rates = list(
        ExchangeRate.objects.filter(is_active=True)
        .select_related("base_currency", "quote_currency")
        .order_by("base_currency__code", "quote_currency__code")
    )
    _apply_rate_trends(rates)
    latest_reviews = Review.objects.select_related("client").all()[:5]
    cities_preview = City.objects.filter(is_active=True).order_by("sort_order", "name")[:8]
    calculator_form = HomeExchangeForm(request.POST or None)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Чтобы создать заявку, войдите в аккаунт.")
            return redirect("auth-login")
        if request.user.role != UserRole.CLIENT:
            messages.error(request, "Создавать заявки может только клиент.")
            return redirect("home")
        if calculator_form.is_valid():
            rate = calculator_form.cleaned_data["rate"]
            send_amount = calculator_form.cleaned_data["computed_send_amount"]
            receive_amount = calculator_form.cleaned_data["computed_receive_amount"]
            order = ExchangeOrder.objects.create(
                client=request.user,
                status="created",
                rate=rate,
                city=calculator_form.cleaned_data["city"],
                contact_phone=calculator_form.cleaned_data["contact_phone"],
                comment=calculator_form.cleaned_data["comment"],
                direction_label=f"{rate.base_currency.code} -> {rate.quote_currency.code}",
                crypto_amount=send_amount,
                fiat_amount=receive_amount,
                total_amount=receive_amount,
                rate_buy_snapshot=rate.buy_rate,
                rate_sell_snapshot=rate.sell_rate,
            )
            messages.success(request, f"Заявка создана. ID: {order.public_id}")
            return redirect("order-detail", public_id=order.public_id)

    now = timezone.now()
    stale_before = now - timedelta(minutes=RATE_STALE_MINUTES)
    rate_options = [
        {
            "id": r.id,
            "base": r.base_currency.code,
            "quote": r.quote_currency.code,
            "buy": format(r.buy_rate, "f"),
            "sell": format(r.sell_rate, "f"),
            "base_is_crypto": r.base_currency.is_crypto,
            "quote_is_crypto": r.quote_currency.is_crypto,
            "updated": r.updated_at.isoformat(),
            "is_stale": r.updated_at < stale_before,
        }
        for r in rates
    ]
    marquee_pairs = [f"{r.base_currency.code} → {r.quote_currency.code}" for r in rates]
    if not marquee_pairs:
        marquee_pairs = [f"{base} → {quote}" for base, quote in DEFAULT_MARQUEE_PAIRS]
    return render(
        request,
        "core/home.html",
        {
            "rates": rates,
            "latest_reviews": latest_reviews,
            "cities_preview": cities_preview,
            "calculator_form": calculator_form,
            "rate_options": rate_options,
            "stale_before": stale_before,
            "marquee_pairs": marquee_pairs,
        },
    )


def rates_partial(request):
    refresh_all_active_rates(min_interval_seconds=300)
    rates = list(ExchangeRate.objects.filter(is_active=True).select_related("base_currency", "quote_currency"))
    _apply_rate_trends(rates)
    stale_before = timezone.now() - timedelta(minutes=RATE_STALE_MINUTES)
    return render(request, "core/partials/rates_table.html", {"rates": rates, "stale_before": stale_before})


def _apply_rate_trends(rates: list[ExchangeRate]) -> None:
    """
    Attach lightweight trend marker for UI: up/down/flat by sell_rate history.
    Uses last two history points; if only one exists, keeps 'flat'.
    """
    rate_ids = [rate.id for rate in rates]
    if not rate_ids:
        return

    histories = (
        ExchangeRateHistory.objects.filter(rate_id__in=rate_ids)
        .only("rate_id", "sell_rate", "created_at")
        .order_by("rate_id", "-created_at")
    )
    recent_by_rate: dict[int, list[ExchangeRateHistory]] = {}
    for entry in histories:
        bucket = recent_by_rate.setdefault(entry.rate_id, [])
        if len(bucket) < 2:
            bucket.append(entry)

    for rate in rates:
        trend = "flat"
        trend_percent = "0.00%"
        entries = recent_by_rate.get(rate.id) or []
        if len(entries) >= 2:
            latest = entries[0].sell_rate
            prev = entries[1].sell_rate
            if latest > prev:
                trend = "up"
            elif latest < prev:
                trend = "down"
            if prev and prev > 0:
                delta_pct = abs((latest - prev) / prev * 100)
                trend_percent = f"{delta_pct:.2f}%"
        rate.trend = trend
        rate.trend_percent = trend_percent


def latest_reviews_partial(request):
    latest_reviews = Review.objects.select_related("client", "order").all()[:5]
    return render(request, "core/partials/latest_reviews.html", {"latest_reviews": latest_reviews})


def reviews_page(request):
    reviews = Review.objects.select_related("client", "order").all()
    return render(request, "core/reviews.html", {"reviews": reviews})


def cities_page(request):
    cities = City.objects.filter(is_active=True).order_by("sort_order", "name")
    return render(request, "core/cities.html", {"cities": cities})


def track_order(request):
    public_id = (request.GET.get("id") or request.POST.get("id") or "").strip()
    order = None
    show_sensitive = False
    if public_id:
        order = (
            ExchangeOrder.objects.filter(public_id__iexact=public_id)
            .select_related("client", "handled_by", "rate__base_currency", "rate__quote_currency", "city")
            .first()
        )
        if order and request.user.is_authenticated:
            if request.user.role in (UserRole.ADMIN, UserRole.MANAGER):
                show_sensitive = True
            elif request.user.role == UserRole.CLIENT and order.client_id == request.user.id:
                show_sensitive = True

    return render(
        request,
        "core/track_order.html",
        {"public_id_query": public_id, "order": order, "show_sensitive": show_sensitive},
    )


@login_required
def order_detail_page(request, public_id):
    order = get_object_or_404(
        ExchangeOrder.objects.select_related("client", "handled_by", "rate__base_currency", "rate__quote_currency", "city"),
        public_id__iexact=public_id.strip(),
    )
    if request.user.role == UserRole.CLIENT and order.client_id != request.user.id:
        messages.error(request, "Это не ваша заявка.")
        return redirect("cabinet")
    can_review = (
        request.user.role == UserRole.CLIENT
        and order.client_id == request.user.id
        and order.status == "completed"
        and not Review.objects.filter(order=order).exists()
    )
    return render(request, "core/order_detail.html", {"order": order, "can_review": can_review})


@login_required
def leave_review_page(request, public_id):
    order = get_object_or_404(
        ExchangeOrder.objects.select_related("client"),
        public_id__iexact=public_id.strip(),
        client=request.user,
    )
    if order.status != "completed":
        messages.error(request, "Отзыв можно оставить только по исполненной заявке.")
        return redirect("order-detail", public_id=order.public_id)
    if Review.objects.filter(order=order).exists():
        messages.info(request, "Отзыв по этой заявке уже отправлен.")
        return redirect("order-detail", public_id=order.public_id)

    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.order = order
        review.client = request.user
        review.save()
        messages.success(request, "Спасибо за отзыв!")
        return redirect("order-detail", public_id=order.public_id)
    return render(request, "core/order_review.html", {"order": order, "form": form})


def articles_page(request):
    articles = NewsItem.objects.filter(is_published=True).select_related("author")
    return render(request, "core/articles.html", {"articles": articles})


def article_detail_page(request, pk):
    article = get_object_or_404(NewsItem.objects.select_related("author"), pk=pk, is_published=True)
    return render(request, "core/article_detail.html", {"article": article})


def _render_legal(request, slug: str, fallback_title: str):
    page = LegalPage.objects.filter(slug=slug).first()
    revision = page.latest_revision() if page else None
    body_html = revision.body if revision else None
    return render(
        request,
        "core/legal_page.html",
        {"page_title": page.title if page else fallback_title, "body": body_html, "revision": revision},
    )


def aml_page(request):
    return _render_legal(request, "aml", "AML / KYC")


def rules_page(request):
    return _render_legal(request, "service-rules", "Правила сервиса")


def legal_page(request, slug: str):
    """Любая юридическая страница по slug (URL: /legal/<slug>/)."""
    page = get_object_or_404(LegalPage, slug=slug)
    return _render_legal(request, page.slug, page.title)


def register_page(request):
    if request.user.is_authenticated:
        return redirect("cabinet")

    form = CustomUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Регистрация успешна. Добро пожаловать!")
        return redirect("cabinet")
    return render(request, "auth/register.html", {"form": form})


def logout_page(request):
    logout(request)
    messages.success(request, "Вы вышли из аккаунта.")
    return redirect("home")


@login_required
def cabinet_page(request):
    if request.user.role == UserRole.MANAGER:
        return redirect("manager-desk")
    if request.user.role == UserRole.ADMIN:
        orders = ExchangeOrder.objects.select_related("client", "handled_by", "rate").all()[:80]
    else:
        orders = ExchangeOrder.objects.select_related("client", "handled_by", "rate").filter(client=request.user)
    return render(request, "core/cabinet.html", {"orders": orders})


@login_required
def create_order_page(request):
    messages.info(request, "Создание заявки перенесено на главную страницу в калькулятор.")
    return redirect("home")


@login_required
@user_passes_test(lambda user: user.role == UserRole.ADMIN)
def admin_panel_page(request):
    now = timezone.now()
    period_start = now - timedelta(days=1)
    previous_period_start = period_start - timedelta(days=1)

    def _trend(current: int, previous: int) -> str:
        if current > previous:
            return "up"
        if current < previous:
            return "down"
        return "flat"

    new_orders_current = ExchangeOrder.objects.filter(status="created").count()
    new_orders_previous = ExchangeOrder.objects.filter(
        status="created",
        created_at__gte=previous_period_start,
        created_at__lt=period_start,
    ).count()

    in_progress_current = ExchangeOrder.objects.filter(status="in_progress").count()
    in_progress_previous = ExchangeOrder.objects.filter(
        status="in_progress",
        created_at__gte=previous_period_start,
        created_at__lt=period_start,
    ).count()

    reviews_current = Review.objects.filter(created_at__gte=period_start).count()
    reviews_previous = Review.objects.filter(
        created_at__gte=previous_period_start,
        created_at__lt=period_start,
    ).count()

    articles_current = NewsItem.objects.filter(is_published=True).count()
    articles_previous = NewsItem.objects.filter(
        is_published=True,
        published_at__gte=previous_period_start,
        published_at__lt=period_start,
    ).count()

    return render(
        request,
        "core/admin_panel.html",
        {
            "orders_in_progress": in_progress_current,
            "new_orders": new_orders_current,
            "reviews_count": Review.objects.count(),
            "published_articles": articles_current,
            "new_orders_trend": _trend(new_orders_current, new_orders_previous),
            "orders_in_progress_trend": _trend(in_progress_current, in_progress_previous),
            "reviews_count_trend": _trend(reviews_current, reviews_previous),
            "published_articles_trend": _trend(articles_current, articles_previous),
        },
    )

from rest_framework import serializers

from rates.models import Currency, ExchangeRate, ExchangeRateHistory


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class ExchangeRateSerializer(serializers.ModelSerializer):
    base_currency_code = serializers.CharField(source="base_currency.code", read_only=True)
    quote_currency_code = serializers.CharField(source="quote_currency.code", read_only=True)

    class Meta:
        model = ExchangeRate
        fields = [
            "id",
            "base_currency",
            "quote_currency",
            "base_currency_code",
            "quote_currency_code",
            "direction_type",
            "margin",
            "buy_rate",
            "sell_rate",
            "source",
            "is_active",
            "updated_at",
        ]


class ExchangeRateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateHistory
        fields = "__all__"

from decimal import Decimal

from rest_framework import serializers

from orders.models import ExchangeOrder


class ExchangeOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeOrder
        fields = "__all__"
        read_only_fields = [
            "public_id",
            "status",
            "client",
            "total_amount",
            "created_at",
            "completed_at",
            "rate_buy_snapshot",
            "rate_sell_snapshot",
            "direction_label",
        ]

    def validate(self, attrs):
        rate = attrs["rate"]
        crypto_amount = attrs["crypto_amount"]
        attrs["fiat_amount"] = Decimal(crypto_amount) * rate.sell_rate
        attrs["total_amount"] = attrs["fiat_amount"]
        attrs["rate_buy_snapshot"] = rate.buy_rate
        attrs["rate_sell_snapshot"] = rate.sell_rate
        attrs["direction_label"] = f"{rate.base_currency.code} -> {rate.quote_currency.code}"
        return attrs


class ExchangeOrderAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeOrder
        fields = "__all__"

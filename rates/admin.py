from django.contrib import admin
from rates.models import Currency, ExchangeRate, ExchangeRateHistory


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_crypto", "is_active")
    search_fields = ("code", "name")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = (
        "base_currency",
        "quote_currency",
        "direction_type",
        "margin",
        "buy_rate",
        "sell_rate",
        "source",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "source", "direction_type")


@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    list_display = ("rate", "buy_rate", "sell_rate", "source", "created_at")
    list_filter = ("source",)

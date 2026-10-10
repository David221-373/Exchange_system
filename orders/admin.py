from django.contrib import admin
from orders.models import ExchangeOrder


@admin.register(ExchangeOrder)
class ExchangeOrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "client",
        "handled_by",
        "status",
        "direction_label",
        "total_amount",
        "city",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("public_id", "client__username", "handled_by__username", "contact_email", "contact_phone")

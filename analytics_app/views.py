from django.db.models import Count, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminRole
from orders.models import ExchangeOrder
from rates.models import Currency
from users.models import UserRole


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        top_buy_currencies = (
            Currency.objects.filter(base_rates__orders__isnull=False)
            .annotate(total=Count("base_rates__orders"))
            .order_by("-total")[:5]
            .values("code", "total")
        )
        top_sell_currencies = (
            Currency.objects.filter(quote_rates__orders__isnull=False)
            .annotate(total=Count("quote_rates__orders"))
            .order_by("-total")[:5]
            .values("code", "total")
        )
        top_clients = (
            ExchangeOrder.objects.filter(client__role=UserRole.CLIENT)
            .values("client__username")
            .annotate(
                total_orders=Count("id"),
                total_fiat=Sum("fiat_amount"),
                total_crypto=Sum("crypto_amount"),
            )
            .order_by("-total_orders")[:10]
        )
        top_managers = (
            ExchangeOrder.objects.exclude(handled_by__isnull=True)
            .values("handled_by__username")
            .annotate(total_orders=Count("id"))
            .order_by("-total_orders")[:10]
        )

        return Response(
            {
                "top_buy_currencies": list(top_buy_currencies),
                "top_sell_currencies": list(top_sell_currencies),
                "top_clients": list(top_clients),
                "top_managers": list(top_managers),
            }
        )

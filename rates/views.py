from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsAdminRole
from rates.models import Currency, ExchangeRate, ExchangeRateHistory
from rates.serializers import CurrencySerializer, ExchangeRateHistorySerializer, ExchangeRateSerializer
from rates.services import refresh_all_active_rates, save_rate_history


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminRole()]
        return [permission() for permission in self.permission_classes]


class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.select_related("base_currency", "quote_currency").all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["base_currency", "quote_currency", "direction_type", "is_active"]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "refresh_from_api"}:
            return [IsAdminRole()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        rate = serializer.save()
        save_rate_history(rate, source=rate.source)

    def perform_update(self, serializer):
        rate = serializer.save()
        save_rate_history(rate, source=rate.source)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminRole])
    def refresh_from_api(self, request, pk=None):
        refresh_all_active_rates(min_interval_seconds=300)
        rate = self.get_object()
        return Response(ExchangeRateSerializer(rate).data)


class ExchangeRateHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExchangeRateHistory.objects.select_related("rate").all()
    serializer_class = ExchangeRateHistorySerializer
    filterset_fields = ["rate", "source"]

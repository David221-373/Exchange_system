from rest_framework.routers import DefaultRouter

from rates.views import CurrencyViewSet, ExchangeRateHistoryViewSet, ExchangeRateViewSet

router = DefaultRouter()
router.register("currencies", CurrencyViewSet, basename="currencies")
router.register("rates", ExchangeRateViewSet, basename="rates")
router.register("rate-history", ExchangeRateHistoryViewSet, basename="rate-history")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from orders.views import ExchangeOrderViewSet

router = DefaultRouter()
router.register("orders", ExchangeOrderViewSet, basename="orders")

urlpatterns = router.urls

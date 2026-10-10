from rest_framework.routers import DefaultRouter

from news.views import NewsItemViewSet

router = DefaultRouter()
router.register("news", NewsItemViewSet, basename="news")

urlpatterns = router.urls

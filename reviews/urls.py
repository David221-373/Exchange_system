from rest_framework.routers import DefaultRouter

from reviews.views import ReviewViewSet

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="reviews")

urlpatterns = router.urls

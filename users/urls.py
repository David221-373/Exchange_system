from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import LoginView, LogoutView, RegisterViewSet, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("register", RegisterViewSet, basename="register")

urlpatterns = [
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", LogoutView.as_view(), name="api-logout"),
] + router.urls

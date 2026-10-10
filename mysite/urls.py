from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

handler400 = "core.error_views.bad_request"
handler403 = "core.error_views.permission_denied"
handler404 = "core.error_views.page_not_found"
handler500 = "core.error_views.server_error"

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="auth-login"),
    path("", include("core.urls")),
    path("api/core/", include("core.api_urls")),
    path("api/users/", include("users.urls")),
    path("api/rates/", include("rates.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/news/", include("news.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/analytics/", include("analytics_app.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

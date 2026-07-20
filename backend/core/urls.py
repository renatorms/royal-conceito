from django.contrib import admin
from django.urls import include, path

from .views import CookieTokenRefreshView, LogoutView, ThrottledTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("produtos.urls")),
    path("api/", include("pedidos.urls")),
    path("api/", include("usuarios.urls")),
    path(
        "api/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("api/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
]

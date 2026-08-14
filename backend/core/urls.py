from django.conf import settings
from django.conf.urls.static import static
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

if settings.DEBUG:
    # Serve MEDIA_ROOT (Produto.imagem uploads) em dev — em produção isso
    # precisa ser servido por um serviço de hospedagem real/proxy dedicado,
    # nunca pelo próprio Django (ver docs/produtos.md).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

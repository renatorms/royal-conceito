from django.urls import path
from rest_framework import routers

from .views import EnderecoViewSet, FreteCalcularView, ItemPedidoViewSet, PedidoViewSet

router = routers.DefaultRouter()

router.register("enderecos", EnderecoViewSet)
router.register("itens", ItemPedidoViewSet)
router.register("pedidos", PedidoViewSet)

# FreteCalcularView isn't a CRUD resource, so it isn't registered on the
# router like the ViewSets above — same pattern as usuarios/urls.py's plain
# `path()` entries for MeView/RegisterView.
urlpatterns = router.urls + [
    path("frete/calcular/", FreteCalcularView.as_view(), name="frete-calcular"),
]

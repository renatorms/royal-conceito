from rest_framework import routers

from .views import EnderecoViewSet, ItemPedidoViewSet, PedidoViewSet

router = routers.DefaultRouter()

router.register("enderecos", EnderecoViewSet)
router.register("itens", ItemPedidoViewSet)
router.register("pedidos", PedidoViewSet)

urlpatterns = router.urls

from django.urls import path
from rest_framework import routers

from .views import (
    EnderecoViewSet,
    FreteCalcularView,
    InfinitePayWebhookView,
    ItemPedidoViewSet,
    PedidoViewSet,
    SolicitacaoTrocaDevolucaoViewSet,
)

router = routers.DefaultRouter()

router.register("enderecos", EnderecoViewSet)
router.register("itens", ItemPedidoViewSet)
router.register("pedidos", PedidoViewSet)
router.register("trocas-devolucoes", SolicitacaoTrocaDevolucaoViewSet)

# FreteCalcularView/InfinitePayWebhookView aren't CRUD resources, so they
# aren't registered on the router like the ViewSets above — same pattern as
# usuarios/urls.py's plain `path()` entries for MeView/RegisterView.
# PedidoViewSet.gerar_link_pagamento (a @action) is registered automatically
# by the router at /pedidos/{id}/gerar-link-pagamento/, no separate path()
# needed.
#
# IMPORTANT: these two literal paths must come BEFORE router.urls, not
# after. DefaultRouter's own detail route matches "pedidos/<anything>/" via
# a pk regex ([^/.]+) — if router.urls were listed first, a request to
# pedidos/webhook-infinitepay/ would match that detail route first (with
# pk="webhook-infinitepay") and never reach this view at all, since Django
# tries urlpatterns in order and stops at the first match.
urlpatterns = [
    path("frete/calcular/", FreteCalcularView.as_view(), name="frete-calcular"),
    path(
        "pedidos/webhook-infinitepay/",
        InfinitePayWebhookView.as_view(),
        name="infinitepay-webhook",
    ),
] + router.urls

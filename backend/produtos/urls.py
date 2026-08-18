from django.urls import path
from rest_framework import routers

from .views import (
    CategoriaMenuView,
    CategoriaViewSet,
    FavoritoViewSet,
    MarcaViewSet,
    ProdutoViewSet,
    VariacaoViewSet,
)

router = routers.DefaultRouter()

router.register("categorias", CategoriaViewSet)
router.register("marcas", MarcaViewSet)
router.register("variacoes", VariacaoViewSet)
router.register("produtos", ProdutoViewSet)
router.register("favoritos", FavoritoViewSet)

urlpatterns = [
    # Not a CRUD resource, so a plain path() rather than a router
    # registration — same pattern as pedidos/urls.py's frete/calcular/.
    # "menu" isn't a registered router prefix (categorias/marcas/produtos/
    # variacoes are), so this can't collide with any router-generated
    # pattern regardless of list order — unlike the webhook-infinitepay
    # case in pedidos/urls.py, there's no need to place this before
    # router.urls for correctness, just kept first for consistency with
    # that same pattern.
    path("menu/categorias/", CategoriaMenuView.as_view(), name="menu-categorias"),
    *router.urls,
]

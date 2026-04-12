from rest_framework import routers

from .views import CategoriaViewSet, MarcaViewSet, ProdutoViewSet, VariacaoViewSet

router = routers.DefaultRouter()

router.register("categorias", CategoriaViewSet)
router.register("marcas", MarcaViewSet)
router.register("variacoes", VariacaoViewSet)
router.register("produtos", ProdutoViewSet)

urlpatterns = router.urls

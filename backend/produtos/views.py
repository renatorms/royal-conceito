from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, Marca, Produto, Variacao
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategoriaSerializer,
    MarcaSerializer,
    ProdutoSerializer,
    VariacaoSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly]


class VariacaoViewSet(viewsets.ModelViewSet):
    queryset = Variacao.objects.all()
    serializer_class = VariacaoSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = (
        Produto.objects.select_related("marca", "categoria")
        .prefetch_related("variacoes")
        .order_by("nome")
    )
    serializer_class = ProdutoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["marca", "categoria"]
    search_fields = ["nome", "marca__nome"]
    ordering_fields = ["nome", "preco"]


class CategoriaMenuView(APIView):
    # Backs the Header's mega menu (frontend `MegaMenu.jsx`): for each
    # Categoria that has at least one Produto, the list of Marcas that have
    # at least one Produto in that specific Categoria — never an empty
    # column (a Categoria with zero Produtos doesn't appear at all) and
    # never a Marca listed under a Categoria it has no stock in.
    #
    # A dedicated read-only endpoint, not assembled client-side from the
    # existing GET /categorias/ + GET /marcas/: those two list *every*
    # Categoria/Marca that exists in the DB, with no way to know which
    # Categoria/Marca combinations actually have products behind them
    # without also walking every Produto — both endpoints are paginated
    # (10/page), so that would mean paging through the entire product
    # catalog on every page load just to build a nav menu. One indexed
    # query on Produto (grouped in Python, not per-Categoria queries) does
    # the same job in a single DB round trip regardless of catalog size.
    #
    # AllowAny, not the project's default IsAuthenticated — same reasoning
    # as ProdutoViewSet's read access via IsAdminOrReadOnly: this is
    # catalog navigation, has to work for an anonymous visitor, and this
    # view only ever does GET, so there's no write path to restrict to
    # staff the way IsAdminOrReadOnly would gate. It also exposes nothing
    # that isn't already readable by anyone via GET /produtos/.
    permission_classes = [AllowAny]

    def get(self, request):
        linhas = (
            Produto.objects.filter(categoria__isnull=False, marca__isnull=False)
            .values("categoria_id", "categoria__nome", "marca_id", "marca__nome")
            .distinct()
            .order_by("categoria__nome", "marca__nome")
        )

        menu = {}
        for linha in linhas:
            categoria_id = linha["categoria_id"]
            entrada = menu.setdefault(
                categoria_id,
                {"id": categoria_id, "nome": linha["categoria__nome"], "marcas": []},
            )
            entrada["marcas"].append({"id": linha["marca_id"], "nome": linha["marca__nome"]})

        # Plain dicts preserve insertion order (Python 3.7+); `linhas` is
        # already ordered by categoria__nome/marca__nome, so this comes out
        # alphabetically sorted on both axes with no extra sort() needed.
        return Response(list(menu.values()))

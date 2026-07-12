from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Categoria, Marca, Produto, Variacao
from .serializers import (
    CategoriaSerializer,
    MarcaSerializer,
    ProdutoSerializer,
    VariacaoSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class VariacaoViewSet(viewsets.ModelViewSet):
    queryset = Variacao.objects.all()
    serializer_class = VariacaoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.select_related("marca", "categoria").prefetch_related(
        "variacoes"
    )
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["marca", "categoria"]
    search_fields = ["nome", "marca__nome"]
    ordering_fields = ["nome", "preco"]

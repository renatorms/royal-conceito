from rest_framework import viewsets

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
    queryset = Produto.objects.select_related("marca", "categoria").prefetch_related(
        "variacoes"
    )
    serializer_class = ProdutoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["marca", "categoria"]
    search_fields = ["nome", "marca__nome"]
    ordering_fields = ["nome", "preco"]

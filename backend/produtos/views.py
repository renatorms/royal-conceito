from rest_framework import viewsets

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


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer


class VariacaoViewSet(viewsets.ModelViewSet):
    queryset = Variacao.objects.all()
    serializer_class = VariacaoSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.select_related("marca", "categoria").prefetch_related(
        "variacoes"
    )
    serializer_class = ProdutoSerializer

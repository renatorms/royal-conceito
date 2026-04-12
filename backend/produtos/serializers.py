from rest_framework import serializers

from .models import Categoria, Marca, Produto, Variacao  # noqa: F401


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"


class VariacaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)

    class Meta:
        model = Variacao
        fields = ["id", "produto", "produto_nome", "tamanho", "estoque"]


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(
        source="categoria.nome", read_only=True, allow_null=True
    )
    # read_only=TRUE: só aparece na saída
    variacoes = VariacaoSerializer(many=True, read_only=True)

    marca_nome = serializers.CharField(
        source="marca.nome", read_only=True, allow_null=True
    )

    class Meta:
        model = Produto
        fields = [
            "id",
            "nome",
            "preco",
            "marca",
            "marca_nome",
            "categoria",
            "categoria_nome",
            "variacoes",
        ]

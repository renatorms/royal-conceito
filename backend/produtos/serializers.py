from rest_framework import serializers

from .models import Categoria, Produto, Variacao  # noqa: F401


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
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

    variacoes = VariacaoSerializer(many=True, read_only=True, source="variacao_set")

    class Meta:
        model = Produto
        fields = [
            "id",
            "nome",
            "preco",
            "marca",
            "categoria",
            "categoria_nome",
            "variacoes",
        ]

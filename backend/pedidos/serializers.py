from rest_framework import serializers

from .models import Endereco, ItemPedido, Pedido  # noqa # noqa: F401


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="variacao.produto.nome", read_only=True)
    produto_tamanho = serializers.CharField(source="variacao.tamanho", read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "pedido",
            "variacao",
            "produto_nome",
            "produto_tamanho",
            "quantidade",
            "preco_unitario",
            "subtotal",
        ]
        read_only_fields = ["subtotal"]


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = ["id", "usuario", "itens", "data_pedido", "total", "status"]
        read_only_fields = ["total"]

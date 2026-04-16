from rest_framework import serializers

from .models import Endereco, ItemPedido, Pedido  # noqa # noqa: F401


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="variacao.produto.nome", read_only=True)
    produto_tamanho = serializers.CharField(source="variacao.tamanho", read_only=True)
    produto_subtotal = serializers.SerializerMethodField()

    def get_produto_subtotal(self, obj):
        return obj.quantidade * obj.preco_unitario

    class Meta:
        model = ItemPedido
        fields = [
            "id",
            "produto_nome",
            "produto_tamanho",
            "quantidade",
            "preco_unitario",
            "produto_subtotal",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = ["id", "cliente", "itens", "data_pedido", "total", "status"]

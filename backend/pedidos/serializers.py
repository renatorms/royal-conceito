from rest_framework import serializers

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido  # noqa # noqa: F401


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"
        read_only_fields = ["usuario"]


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
        read_only_fields = ["subtotal", "preco_unitario"]


class ItemPedidoCriacaoSerializer(serializers.Serializer):
    """Write-only shape for creating an ItemPedido inline with its Pedido.

    Deliberately a plain Serializer, not ItemPedidoSerializer reused as
    write-only: ItemPedidoSerializer requires `pedido` (there isn't one yet
    at this point) and exposes read-only derived fields (produto_nome,
    subtotal, ...) that make no sense on input. `preco_unitario` is not
    accepted here either — PedidoViewSet.perform_create() always sets it
    server-side from `variacao.produto.preco`, same rule as
    ItemPedidoViewSet.perform_create().
    """

    variacao = serializers.PrimaryKeyRelatedField(queryset=Variacao.objects.all())
    quantidade = serializers.IntegerField(min_value=1)


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    # Write-only counterpart to `itens`: lets POST /pedidos/ create the order
    # and its lines atomically in one call (see PedidoViewSet.perform_create()).
    # Kept as a separate field rather than making `itens` writable, since
    # `itens` is a nested ItemPedidoSerializer built for *reading* an already
    # -persisted line (id, produto_nome, subtotal, ...) — reusing it for input
    # would require a pedido that doesn't exist yet and accept fields clients
    # must never set (preco_unitario, subtotal). Optional/defaults to empty,
    # so the old "POST /pedidos/ empty, then POST /itens/ per line" flow keeps
    # working unchanged.
    itens_criacao = ItemPedidoCriacaoSerializer(many=True, write_only=True, required=False)
    endereco_detalhe = EnderecoSerializer(source="endereco", read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "usuario",
            "itens",
            "itens_criacao",
            "endereco",
            "endereco_detalhe",
            "data_pedido",
            "total",
            "status",
        ]
        # `usuario` is read_only for the same reason as Endereco.usuario
        # (pedidos/serializers.py::EnderecoSerializer) — without it, a
        # PUT/PATCH to /api/pedidos/{id}/ could reassign an existing order
        # (and its whole item history) to a different user's account, since
        # IsDonorOrStaff's object-level check only confirms the caller owns
        # the *current* Pedido, not what values the request can write.
        read_only_fields = ["total", "usuario"]

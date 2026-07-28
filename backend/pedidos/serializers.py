from rest_framework import serializers

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido  # noqa # noqa: F401


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"
        read_only_fields = ["usuario"]


class ItemPedidoSerializer(serializers.ModelSerializer):
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
        # produto_nome/produto_tamanho used to be declared above as
        # serializers.CharField(source="variacao.produto.nome"/"variacao.
        # tamanho", read_only=True) — derived live from the *current*
        # Variacao/Produto on every read, not from ItemPedido's own columns.
        # That meant editing a Variacao's produto or tamanho after the sale
        # silently rewrote how every past order that sold it was displayed,
        # even though the sale itself never changed (see CLAUDE.md for the
        # incident this caused). Both are now real ItemPedido columns,
        # frozen once at creation time in ItemPedidoViewSet.perform_create()
        # and the itens_criacao loop in PedidoViewSet.perform_create() —
        # DRF's ModelSerializer picks them up automatically from Meta.model
        # now that they're real fields, no explicit declaration needed; the
        # field names in the API response are unchanged, so no frontend
        # change was needed either. read_only for the same reason as
        # preco_unitario/subtotal: always set by the backend, never by the
        # client.
        read_only_fields = ["subtotal", "preco_unitario", "produto_nome", "produto_tamanho"]


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


class FreteItemSerializer(serializers.Serializer):
    """One cart line for POST /frete/calcular/. Deliberately not shared with
    ItemPedidoCriacaoSerializer above despite today's identical shape: this
    one is never used to create anything, only to look up a Variacao's
    weight/dimensions/price for a shipping quote — a future change to
    order-item creation input shouldn't accidentally affect the freight
    endpoint, or vice versa."""

    variacao = serializers.PrimaryKeyRelatedField(queryset=Variacao.objects.all())
    quantidade = serializers.IntegerField(min_value=1)


class FreteCalcularSerializer(serializers.Serializer):
    """Input shape for POST /frete/calcular/. `cep_destino` accepts either
    "01153-000" or "01153000" — pedidos/services/superfrete.py strips
    non-digits before sending it to the SuperFrete API, so validation here
    only checks a plausible length, not the exact format."""

    cep_destino = serializers.CharField(max_length=9, min_length=8)
    itens = FreteItemSerializer(many=True, allow_empty=False)


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

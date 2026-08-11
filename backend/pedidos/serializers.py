from rest_framework import serializers

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido, SolicitacaoTrocaDevolucao  # noqa # noqa: F401


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


class FreteSelecionadoSerializer(serializers.Serializer):
    """Write-only shape for the freight option chosen at checkout, mirroring
    the response shape of POST /frete/calcular/ ({id, nome, transportadora,
    preco, prazo_dias} — see calcular_frete() in
    pedidos/services/superfrete.py). `id` (SuperFrete's own option id) is
    deliberately not declared here: it isn't meaningful after the sale, only
    nome/transportadora/preco/prazo_dias are frozen onto Pedido as a
    checkout-time snapshot (see PedidoViewSet.perform_create() and
    CLAUDE.md). A plain (non-Model) Serializer ignores unknown input keys by
    default, so the frontend can keep sending the whole option object as-is,
    `id` included, with no error."""

    nome = serializers.CharField(max_length=50)
    transportadora = serializers.CharField(max_length=100)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)
    prazo_dias = serializers.IntegerField(min_value=0)


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
    # must never set (preco_unitario, subtotal). `required=False` here is
    # about *updates*, not creation: PATCH/PUT never touches this field (see
    # PedidoViewSet.perform_update()), so it must stay optional for those to
    # keep working. On creation, PedidoViewSet.perform_create() rejects an
    # empty/missing list outright (a Pedido with zero items is no longer a
    # reachable state via this API) — done there rather than as
    # `required=True, allow_empty=False` on the field itself (which would
    # also wrongly apply to updates), and rather than in this serializer's
    # own validate() (tried first, reverted: DRF's as_serializer_error()
    # always wraps a dict-shaped ValidationError raised inside a
    # serializer's validate() into `{"detail": [...]}` — a list — breaking
    # the bare-string `{"detail": "..."}` shape every other error in this
    # API uses, confirmed via curl).
    itens_criacao = ItemPedidoCriacaoSerializer(many=True, write_only=True, required=False)
    endereco_detalhe = EnderecoSerializer(source="endereco", read_only=True)
    # Write-only counterpart to frete_valor/frete_nome/frete_transportadora/
    # frete_prazo_dias, same shape as itens_criacao above: lets POST
    # /pedidos/ pass the chosen SuperFrete option to be frozen onto the new
    # Pedido in one call, without exposing those four real columns as
    # directly writable (they're backend-set only, see read_only_fields
    # below — same rule as preco_unitario/produto_nome on ItemPedido).
    frete_selecionado = FreteSelecionadoSerializer(write_only=True, required=False)

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
            "frete_selecionado",
            "frete_valor",
            "frete_nome",
            "frete_transportadora",
            "frete_prazo_dias",
        ]
        # `usuario` is read_only for the same reason as Endereco.usuario
        # (pedidos/serializers.py::EnderecoSerializer) — without it, a
        # PUT/PATCH to /api/pedidos/{id}/ could reassign an existing order
        # (and its whole item history) to a different user's account, since
        # IsDonorOrStaff's object-level check only confirms the caller owns
        # the *current* Pedido, not what values the request can write.
        # frete_valor/frete_nome/frete_transportadora/frete_prazo_dias are
        # read_only for the same reason as preco_unitario/produto_nome on
        # ItemPedidoSerializer: always set by the backend
        # (PedidoViewSet.perform_create(), from frete_selecionado), never by
        # the client directly — a raw {"frete_valor": 0.01} in the payload
        # is silently ignored, same as a forged preco_unitario would be.
        read_only_fields = [
            "total",
            "usuario",
            "frete_valor",
            "frete_nome",
            "frete_transportadora",
            "frete_prazo_dias",
        ]


class SolicitacaoTrocaDevolucaoSerializer(serializers.ModelSerializer):
    # Três campos read-only derivados de item_pedido, só para exibição —
    # mesmo padrão de ProdutoSerializer.categoria_nome/marca_nome e
    # PedidoSerializer.endereco_detalhe: o cliente já manda `item_pedido`
    # (um id) na criação, mas a tela de "minhas solicitações" precisa saber
    # de qual pedido/produto/tamanho se trata sem um segundo round-trip por
    # solicitação.
    pedido_id = serializers.IntegerField(source="item_pedido.pedido_id", read_only=True)
    produto_nome = serializers.CharField(source="item_pedido.produto_nome", read_only=True)
    produto_tamanho = serializers.CharField(source="item_pedido.produto_tamanho", read_only=True)

    class Meta:
        model = SolicitacaoTrocaDevolucao
        fields = [
            "id",
            "item_pedido",
            "pedido_id",
            "produto_nome",
            "produto_tamanho",
            "tipo",
            "motivo",
            "status",
            "criado_em",
            "atualizado_em",
        ]
        # `status` é sempre read_only aqui — nenhum cliente (nem staff) pode
        # mudar o status de uma solicitação através desta API hoje. Não é um
        # descuido: staff ainda pode revisar/mudar o status pelo Django
        # Admin (ver SolicitacaoTrocaDevolucaoAdmin, pedidos/admin.py) — um
        # endpoint dedicado de transição de status (com as regras de quem
        # pode mudar o quê, notificação ao cliente, etc.) fica para uma fase
        # futura de "área do lojista", fora do escopo desta primeira versão
        # funcional da feature. Ver CLAUDE.md.
        read_only_fields = ["status", "criado_em", "atualizado_em"]

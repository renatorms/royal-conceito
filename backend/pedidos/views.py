import logging

from django.conf import settings
from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido, SolicitacaoTrocaDevolucao
from .permissions import IsDonorOrStaff, IsItemDonorOrStaff, IsSolicitacaoDonorOrStaff
from .serializers import (
    EnderecoSerializer,
    FreteCalcularSerializer,
    ItemPedidoSerializer,
    PedidoSerializer,
    SolicitacaoTrocaDevolucaoSerializer,
)
from .services.infinitepay import (
    InfinitePayConfiguracaoError,
    InfinitePayIndisponivelError,
    criar_link_pagamento,
    verificar_pagamento,
)
from .services.superfrete import (
    SuperFreteConfiguracaoError,
    SuperFreteDestinoInvalidoError,
    SuperFreteIndisponivelError,
    calcular_frete,
)
from .signals import recalcula_total_pedido

logger = logging.getLogger(__name__)


class EnderecoViewSet(viewsets.ModelViewSet):
    queryset = Endereco.objects.all()
    serializer_class = EnderecoSerializer
    permission_classes = [IsAuthenticated, IsDonorOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Endereco.objects.all()
        return Endereco.objects.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        # `usuario` is read_only on EnderecoSerializer, so a payload can't
        # reassign it anyway — this is defense in depth. Re-assert the
        # *existing* owner (not self.request.user): IsDonorOrStaff lets staff
        # edit any address, and forcing self.request.user here would silently
        # reassign someone else's address to the staff member doing the edit.
        serializer.save(usuario=serializer.instance.usuario)

    def perform_destroy(self, instance):
        # Endereco.usuario aside, Pedido.endereco is PROTECT (see CLAUDE.md) —
        # deleting an address still linked to any order raises ProtectedError.
        # Without this, that bubbles up as an unhandled 500; catch it and
        # return the same {"detail": ...} shape used elsewhere in this API.
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                {
                    "detail": (
                        "Este endereço não pode ser excluído porque está "
                        "vinculado a um ou mais pedidos."
                    )
                }
            )


class ItemPedidoViewSet(viewsets.ModelViewSet):
    queryset = ItemPedido.objects.all()
    serializer_class = ItemPedidoSerializer
    permission_classes = [IsAuthenticated, IsItemDonorOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ItemPedido.objects.all()
        return ItemPedido.objects.filter(pedido__usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        pedido = serializer.validated_data["pedido"]
        if not user.is_staff and pedido.usuario != user:
            raise PermissionDenied("Você não pode adicionar itens a um pedido que não é seu.")

        variacao_id = serializer.validated_data["variacao"].pk
        quantidade = serializer.validated_data["quantidade"]

        # Authoritative check, inside transaction.atomic(): ATOMIC_REQUESTS is
        # off, so without this wrap an ItemPedido INSERT commits immediately
        # on .save(), before the post_save signal (and its own separate
        # @transaction.atomic block) even runs — raising ValidationError from
        # within the signal would return a clean 400, but the invalid row
        # itself would already be committed by then (orphaned, never
        # reflected in Pedido.total since diminui_estoque's exception stops
        # atualiza_total_pedido from running). Wrapping the check *and* the
        # save in one atomic() block means a rejection anywhere inside it —
        # including from the signal's own backstop check, e.g. if this
        # request loses a race against a concurrent one for the same
        # Variacao — rolls back the INSERT too, so no orphaned row survives
        # either way.
        #
        # select_for_update() re-fetches rather than trusting
        # serializer.validated_data["variacao"] (resolved once, up front,
        # during is_valid(), with no lock): it locks the row for the rest of
        # this transaction on backends that support it (not SQLite — see
        # signals.py::diminui_estoque, which re-decrements via an atomic
        # conditional UPDATE regardless, since that lock is a no-op here in
        # dev). The signal's own check stays in place as a defense-in-depth
        # backstop for creation paths that don't go through this view (e.g.
        # the Django admin's ItemPedidoInline).
        with transaction.atomic():
            variacao = Variacao.objects.select_for_update().get(pk=variacao_id)
            if variacao.estoque < quantidade:
                raise ValidationError(
                    {"detail": f"Estoque insuficiente. Restam apenas {variacao.estoque} unidades."}
                )

            # produto_nome/produto_tamanho are frozen here, at creation, same
            # as preco_unitario — see CLAUDE.md and the ItemPedido model
            # comment for why: without this, a later edit to Variacao.produto
            # or Variacao.tamanho would silently rewrite how this sale is
            # displayed forever after, even though the sale itself never
            # changed.
            serializer.save(
                preco_unitario=variacao.produto.preco,
                produto_nome=variacao.produto.nome,
                produto_tamanho=variacao.tamanho,
            )


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated, IsDonorOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Pedido.objects.all()
        return Pedido.objects.filter(usuario=user)

    def perform_create(self, serializer):
        # A Pedido with zero items used to be reachable on purpose (the old
        # "create empty, then POST /itens/ per line" flow, replaced by the
        # atomic itens_criacao path below). Now that every real caller always
        # sends items — Checkout.jsx always has a non-empty cart by the time
        # it calls this, and the Django admin creates Pedido + ItemPedido
        # together through its own form/inline, never through this API — an
        # empty/missing itens_criacao is a leftover gap, not a use case, so
        # it's rejected outright before anything is created.
        #
        # Checked here, first thing, rather than as `required=True,
        # allow_empty=False` on PedidoSerializer.itens_criacao: that field is
        # also used by updates (where it's legitimately absent — see
        # perform_update(), which never touches it), so the field itself has
        # to stay optional; the non-empty rule only applies to creation.
        # Also checked here rather than in the serializer's own validate()
        # (tried first, reverted): DRF's as_serializer_error() always wraps a
        # dict-shaped ValidationError raised inside a serializer's validate()
        # into `{"detail": [...]}` — a list — instead of the bare
        # `{"detail": "..."}` string every other error in this API uses;
        # raising directly in the view, like the stock checks below already
        # do, avoids that wrapping and keeps the shape consistent (confirmed
        # via curl — see CLAUDE.md).
        itens_data = serializer.validated_data.pop("itens_criacao", None)
        if not itens_data:
            raise ValidationError({"detail": "Um pedido precisa ter pelo menos um item."})

        endereco = serializer.validated_data.get("endereco")
        user = self.request.user
        if endereco and not user.is_staff and endereco.usuario != user:
            raise PermissionDenied("Você não pode vincular a este pedido um endereço que não é seu.")

        # POST /pedidos/ creates the Pedido and every ItemPedido line in a
        # single DB transaction. `itens_data` is guaranteed non-empty here —
        # the check above already rejected an empty/missing list. Popped out
        # of validated_data before serializer.save() because it isn't a real
        # Pedido field — PedidoSerializer.create() (ModelSerializer's
        # default) would otherwise pass it straight to
        # Pedido.objects.create(**validated_data) and blow up on an
        # unexpected keyword argument.

        # Same shape as itens_data above: frete_selecionado isn't a real
        # Pedido field either (it's the write-only nested option the client
        # sent), so it's popped out and its four sub-values are passed as
        # explicit save() kwargs onto the real, backend-owned columns
        # instead — same pattern already used for preco_unitario/produto_nome
        # in ItemPedidoViewSet.perform_create(). Omitted entirely (not just
        # falsy) when the client didn't send a freight option — e.g. the
        # SuperFrete quote failed and checkout proceeded without blocking
        # (see CLAUDE.md) — leaving all four columns at their null default.
        frete_data = serializer.validated_data.pop("frete_selecionado", None)
        frete_kwargs = (
            {
                "frete_valor": frete_data["preco"],
                "frete_nome": frete_data["nome"],
                "frete_transportadora": frete_data["transportadora"],
                "frete_prazo_dias": frete_data["prazo_dias"],
            }
            if frete_data
            else {}
        )

        with transaction.atomic():
            serializer.save(usuario=self.request.user, **frete_kwargs)
            pedido = serializer.instance

            for item in itens_data:
                # select_for_update() rather than trusting the
                # PrimaryKeyRelatedField instance from validated_data: that
                # was resolved once, up front, when the whole payload was
                # validated, with no lock. Re-fetching (locked, on backends
                # that support it — see signals.py::diminui_estoque for why
                # SQLite doesn't) is what makes a repeated variacao id within
                # this same itens_criacao batch see the previous line's
                # decrement rather than the pre-request stock level; it's
                # also what the outer-scope race (a *different* request
                # competing for the same Variacao) needs, on backends where
                # the lock actually holds.
                variacao = Variacao.objects.select_for_update().get(pk=item["variacao"].pk)
                quantidade = item["quantidade"]

                # Same authoritative-check-before-create pattern as
                # ItemPedidoViewSet.perform_create() (see the comment there
                # for why the check has to happen before creating the row,
                # not only inside the diminui_estoque signal). Here the
                # outer transaction.atomic() would actually catch that case
                # too — raising anywhere in this block, including from
                # inside the signal, rolls back the whole Pedido along with
                # every ItemPedido and stock decrement already applied in
                # this loop — but checking explicitly first keeps the two
                # creation paths consistent and gives a message naming the
                # specific item, useful here since a batch can fail on any
                # one of several lines.
                if variacao.estoque < quantidade:
                    raise ValidationError(
                        {
                            "detail": (
                                f"Estoque insuficiente para {variacao.produto.nome} - "
                                f"{variacao.tamanho}. Restam apenas {variacao.estoque} unidades."
                            )
                        }
                    )

                # produto_nome/produto_tamanho frozen at creation — same
                # reasoning as ItemPedidoViewSet.perform_create() above.
                ItemPedido.objects.create(
                    pedido=pedido,
                    variacao=variacao,
                    quantidade=quantidade,
                    preco_unitario=variacao.produto.preco,
                    produto_nome=variacao.produto.nome,
                    produto_tamanho=variacao.tamanho,
                )

            # Each ItemPedido.objects.create() above already re-triggers
            # atualiza_total_pedido (post_save signal), which recomputes
            # total from frete_valor already set on this same `pedido`
            # instance — so, now that itens_data is always non-empty (see
            # the check at the top of this method), this call is always
            # redundant on the create path. Kept anyway: cheap, idempotent,
            # and a harmless safety net rather than something worth deleting.
            recalcula_total_pedido(pedido)

    def perform_update(self, serializer):
        # Same endereco-ownership check as perform_create() above, replicated
        # for updates — it had never been, so a PUT/PATCH could link an
        # existing Pedido to another user's saved address with zero
        # validation, leaking that address's existence/contents via
        # endereco_detalhe on every future read of the order. Checked against
        # serializer.instance.usuario (the Pedido's *existing* owner), not
        # self.request.user: IsDonorOrStaff lets staff edit any Pedido, and a
        # staff member fixing a customer's order should be able to attach an
        # address that belongs to *that customer*, not be limited to their
        # own — same reasoning as EnderecoViewSet.perform_update() re-
        # asserting the existing owner rather than the requester.
        endereco = serializer.validated_data.get("endereco")
        user = self.request.user
        pedido_usuario = serializer.instance.usuario
        if endereco and not user.is_staff and endereco.usuario != pedido_usuario:
            raise PermissionDenied("Você não pode vincular a este pedido um endereço que não é seu.")

        # `usuario` is read_only on PedidoSerializer, so a payload can't
        # reassign it anyway — this is defense in depth, same pattern as
        # EnderecoViewSet.perform_update().
        serializer.save(usuario=pedido_usuario)

    @action(detail=True, methods=["post"], url_path="gerar-link-pagamento")
    def gerar_link_pagamento(self, request, pk=None):
        # A separate action the frontend calls right after POST /pedidos/
        # succeeds, not folded into perform_create() above — deliberate.
        # Pedido creation already does the part that actually needs to be
        # atomic and hard to retry safely (locking Variacao rows, decrementing
        # stock, freezing preco_unitario/produto_nome — see perform_create()
        # and CLAUDE.md). Generating a payment link is a call to a third-party
        # API with none of that: it doesn't touch stock, isn't tied to the
        # same DB transaction, and — like the SuperFrete quote in
        # FreteCalcularView — can fail transiently for reasons that have
        # nothing to do with whether the order itself is valid. Coupling the
        # two (e.g. calling InfinitePay from inside perform_create()'s
        # transaction.atomic() block) would mean a slow/flaky InfinitePay
        # response either rolls back a perfectly valid, already-decremented
        # order, or leaves the transaction open for the duration of an
        # external HTTP call — both worse than the order existing on its own.
        # get_object() already runs IsDonorOrStaff.has_object_permission(),
        # so this can't be called on someone else's Pedido.
        pedido = self.get_object()

        if pedido.status != "novo":
            # Already paid (or being handled another way, e.g. cancelado) —
            # generating a fresh checkout link for it would be misleading at
            # best (a second payment for an already-confirmed order) and
            # actively wrong at worst.
            raise ValidationError(
                {"detail": "Este pedido não está aguardando pagamento."}
            )

        if pedido.link_pagamento_url:
            # Idempotency fix (see CLAUDE.md, "InfinitePay Payment
            # Integration" — this used to be an open gap): a link already
            # exists for this Pedido from a previous call (the frontend's
            # own "Tentar novamente" retry, a double-click, or any repeat
            # call for a still-"novo" order) — reuse it instead of minting a
            # new one via a second POST /links call. No expiration/
            # invalidation mechanism for a checkout link is documented by
            # InfinitePay (Central de Ajuda checked directly for this fix —
            # no article on link validity/cancellation found; the technical
            # API reference at docs.infinitepay.io could not be reached to
            # check further — see CLAUDE.md), so validity is tied to
            # `status` instead: the guard above already blocks generating
            # (or reusing) a link once the Pedido leaves "novo", which is
            # exactly when this cached link stops being relevant.
            return Response({"url": pedido.link_pagamento_url})

        itens = [
            {
                "descricao": (
                    f"{item.produto_nome} - Tam. {item.produto_tamanho}"
                    if item.produto_nome
                    else f"Item do pedido #{pedido.id}"
                ),
                "quantidade": item.quantidade,
                # preco_unitario is a DecimalField(decimal_places=2) — already
                # exact to the cent, so multiplying by 100 and truncating to
                # int is exact too (no float rounding involved at any point).
                "preco_centavos": int(item.preco_unitario * 100),
            }
            for item in pedido.itens.all()
        ]
        if pedido.frete_valor:
            # The freight snapshot is part of Pedido.total (see
            # recalcula_total_pedido() in signals.py) but isn't an ItemPedido
            # — without a line for it here, the amount charged via
            # InfinitePay would fall short of pedido.total by exactly the
            # freight value. Included as its own line, named after the
            # carrier/service actually chosen at checkout, same snapshot
            # already frozen onto the Pedido.
            itens.append(
                {
                    "descricao": f"Frete ({pedido.frete_nome or 'entrega'})",
                    "quantidade": 1,
                    "preco_centavos": int(pedido.frete_valor * 100),
                }
            )

        try:
            url = criar_link_pagamento(
                order_nsu=str(pedido.id),
                itens=itens,
                redirect_url=f"{settings.FRONTEND_URL}/pedido-confirmado?pedidoId={pedido.id}",
                webhook_url=f"{settings.BACKEND_URL}/api/pedidos/webhook-infinitepay/",
            )
        except InfinitePayConfiguracaoError as exc:
            logger.error("Link de pagamento: configuração da InfinitePay inválida: %s", exc)
            raise ServicoIndisponivel(
                {
                    "detail": (
                        "Não foi possível gerar o link de pagamento no momento. "
                        "Tente novamente em instantes."
                    )
                }
            )
        except InfinitePayIndisponivelError as exc:
            logger.error("Link de pagamento: falha ao chamar a InfinitePay: %s", exc)
            raise ServicoIndisponivel(
                {
                    "detail": (
                        "Não foi possível gerar o link de pagamento no momento. "
                        "Tente novamente em instantes."
                    )
                }
            )

        pedido.link_pagamento_url = url
        pedido.save(update_fields=["link_pagamento_url"])
        return Response({"url": url})


class SolicitacaoTrocaDevolucaoViewSet(viewsets.ModelViewSet):
    queryset = SolicitacaoTrocaDevolucao.objects.all()
    serializer_class = SolicitacaoTrocaDevolucaoSerializer
    permission_classes = [IsAuthenticated, IsSolicitacaoDonorOrStaff]

    def get_queryset(self):
        # select_related percorrendo até Pedido/Produto: toda solicitação
        # exibida numa lista precisa de pedido_id/produto_nome/
        # produto_tamanho (ver SolicitacaoTrocaDevolucaoSerializer) — sem
        # isso, cada linha da lista dispararia uma query extra pra resolver
        # item_pedido.pedido_id/produto_nome, o mesmo problema de N+1 que
        # ProdutoViewSet já evita com select_related/prefetch_related.
        qs = SolicitacaoTrocaDevolucao.objects.select_related(
            "item_pedido__pedido", "item_pedido__variacao"
        )
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(item_pedido__pedido__usuario=user)

    def perform_create(self, serializer):
        # Mesma dupla checagem de ItemPedidoViewSet.perform_create() acima:
        # `item_pedido` chega como um PrimaryKeyRelatedField sobre
        # ItemPedido.objects.all() (não filtrado por dono já na definição do
        # campo — DRF resolve o queryset uma vez, na definição da classe,
        # antes de existir qualquer `request`), então a posse só pode ser
        # confirmada aqui, depois da validação básica.
        item_pedido = serializer.validated_data["item_pedido"]
        user = self.request.user
        if not user.is_staff and item_pedido.pedido.usuario != user:
            # 403, não 404: mesmo padrão já usado em ItemPedidoViewSet/
            # PedidoViewSet.perform_create() para o mesmo tipo de violação
            # (tentar criar algo vinculado a um recurso de outro usuário) —
            # aqui não há get_queryset() filtrando o item_pedido de entrada
            # antes da permissão rodar (diferente de GET/detail, onde
            # get_queryset() já esconde o registro e produz um 404 "de
            # graça"), então a checagem explícita decide o código de status.
            raise PermissionDenied(
                "Você não pode solicitar troca/devolução de um item que não é seu."
            )

        if item_pedido.pedido.status != "entregue":
            # Regra de negócio central da feature: só pedidos já entregues
            # podem gerar uma solicitação de troca/devolução — pedir troca
            # de algo que ainda nem chegou não faz sentido. Checado aqui,
            # não no serializer/validate() (mesmo motivo documentado em
            # PedidoViewSet.perform_create() para a checagem de
            # itens_criacao vazio: DRF embrulha um ValidationError levantado
            # dentro de validate() como `{"detail": [...]}`, uma lista, em
            # vez do `{"detail": "..."}` que todo outro erro desta API usa).
            raise ValidationError(
                {
                    "detail": (
                        "Só é possível solicitar troca ou devolução de itens de "
                        "pedidos já entregues."
                    )
                }
            )

        serializer.save()


class ServicoIndisponivel(APIException):
    # Plain APIException defaults to a 500; a failed *external* dependency
    # (SuperFrete down, our own token misconfigured, a network blip) is a
    # 503 — not a bug in this API, and not the client's fault either, so
    # distinct from both ValidationError (400, client's input) and an
    # unhandled 500 (our own bug).
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "servico_indisponivel"


class FreteCalcularView(APIView):
    # Público (AllowAny, not the project's default IsAuthenticated) —
    # deliberate: shipping cost needs to be visible in the cart before a
    # visitor logs in (Carrinho.jsx is itself a public route), and this
    # endpoint doesn't read or write anything user-specific — only
    # Variacao's own weight/dimensions/price, already public data (GET
    # /api/produtos/ is public too). The one real risk of leaving it public
    # is abuse: each call is a real request against SuperFrete's API using
    # our token, so it's throttled the same way /api/token/ and
    # /api/registro/ already are (public + a cost/abuse surface) — see
    # DEFAULT_THROTTLE_RATES in core/settings.py.
    permission_classes = [AllowAny]
    throttle_scope = "frete"

    def post(self, request):
        serializer = FreteCalcularSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produtos = [
            {
                "altura": item["variacao"].altura,
                "largura": item["variacao"].largura,
                "comprimento": item["variacao"].comprimento,
                "peso": item["variacao"].peso,
                "quantidade": item["quantidade"],
                "valor": item["variacao"].produto.preco,
            }
            for item in serializer.validated_data["itens"]
        ]

        # Each SuperFreteError subclass gets a distinct, deliberately-chosen
        # response — see pedidos/services/superfrete.py for why they're
        # split this way. The raw exception (which may include SuperFrete's
        # own response body) is only ever logged, never put in the response
        # body sent to the client.
        try:
            opcoes = calcular_frete(serializer.validated_data["cep_destino"], produtos)
        except SuperFreteDestinoInvalidoError as exc:
            logger.info("Frete: CEP de destino rejeitado pela SuperFrete: %s", exc)
            raise ValidationError(
                {"detail": "CEP de destino inválido ou fora da área de cobertura."}
            )
        except (SuperFreteConfiguracaoError, SuperFreteIndisponivelError) as exc:
            logger.error("Frete: falha ao calcular frete via SuperFrete: %s", exc)
            raise ServicoIndisponivel(
                {
                    "detail": (
                        "Não foi possível calcular o frete no momento. "
                        "Tente novamente em instantes."
                    )
                }
            )

        return Response(opcoes)


class InfinitePayWebhookView(APIView):
    # Público (AllowAny) por necessidade, não por escolha de design — quem
    # chama este endpoint é o servidor da InfinitePay, que não tem (nem pode
    # ter) o cookie JWT de nenhum usuário do site. Mesmo padrão de
    # "autenticação não é o mecanismo de confiança aqui" do
    # FreteCalcularView, mas por um motivo mais sério: a InfinitePay não
    # assina o webhook de forma nenhuma (sem HMAC, sem secret, sem header
    # verificável — confirmado consultando a documentação deles, ver
    # CLAUDE.md), então NADA no corpo desta requisição pode ser confiado só
    # por ter chegado aqui. Qualquer um que descubra esta URL pode enviar um
    # POST forjado alegando que um pedido foi pago.
    #
    # A confiança real vem de verificar_pagamento() (services/infinitepay.py)
    # logo abaixo: em vez de confiar no campo "paid"/valor do corpo do
    # webhook, este view liga de volta pra própria API da InfinitePay
    # (payment_check) usando o transaction_nsu/slug que o webhook alegou, e
    # só marca o pedido como confirmado se a InfinitePay concordar, no seu
    # próprio registro, que aquela transação específica foi paga — e pelo
    # valor esperado. Isso fecha o ataque óbvio (forjar um POST alegando
    # pagamento) e também um mais sutil: como o handle é público e
    # order_nsu não é validado por nenhum token do lado da InfinitePay,
    # qualquer pessoa pode gerar seu próprio link de pagamento citando o
    # order_nsu de um pedido alheio e de fato pagá-lo — só que por um valor
    # menor (ex: R$0,01). payment_check() devolve o valor realmente pago
    # daquela transação, e ele é comparado contra pedido.total abaixo antes
    # de confirmar — um pagamento genuíno mas por um valor errado não
    # confirma o pedido.
    permission_classes = [AllowAny]
    throttle_scope = "infinitepay_webhook"

    def post(self, request):
        order_nsu = request.data.get("order_nsu")
        transaction_nsu = request.data.get("transaction_nsu")
        invoice_slug = request.data.get("invoice_slug")

        if not order_nsu or not transaction_nsu:
            logger.warning(
                "Webhook InfinitePay: payload sem order_nsu/transaction_nsu: %s",
                request.data,
            )
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pedido = Pedido.objects.get(pk=order_nsu)
        except (Pedido.DoesNotExist, ValueError, TypeError):
            # ValueError/TypeError: order_nsu não é um id numérico válido —
            # não deveria acontecer com um order_nsu que realmente veio de um
            # link gerado por nós (sempre str(pedido.id)), mas não é motivo
            # pra estourar um 500 num endpoint público.
            logger.warning("Webhook InfinitePay: order_nsu %r não corresponde a nenhum Pedido.", order_nsu)
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

        if pedido.status != "novo":
            # Já confirmado (webhook duplicado/reentregue — a InfinitePay
            # pode reenviar) ou em outro estado (cancelado etc). Idempotente:
            # responde sucesso sem re-verificar nem alterar nada, evitando
            # tanto uma segunda chamada desnecessária ao payment_check quanto
            # reabrir um pedido que já saiu do estado "aguardando pagamento".
            return Response({"success": True})

        try:
            resultado = verificar_pagamento(
                order_nsu=order_nsu, transaction_nsu=transaction_nsu, slug=invoice_slug
            )
        except (InfinitePayConfiguracaoError, InfinitePayIndisponivelError) as exc:
            logger.error(
                "Webhook InfinitePay: falha ao verificar pagamento do pedido %s: %s",
                pedido.id,
                exc,
            )
            # 503, não 400: o problema é nosso/da InfinitePay no momento, não
            # do payload recebido — vale a pena a InfinitePay tentar de novo
            # mais tarde (comportamento documentado: 400 aciona retry; um 5xx
            # também é tratado como falha temporária pela maioria dos
            # provedores de webhook).
            return Response({"success": False}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        valor_esperado_centavos = int(pedido.total * 100)
        if not resultado["paid"] or resultado["amount_centavos"] != valor_esperado_centavos:
            logger.warning(
                "Webhook InfinitePay: payment_check não confirmou pagamento esperado do "
                "pedido %s (esperado %s centavos, resultado: %s).",
                pedido.id,
                valor_esperado_centavos,
                resultado,
            )
            # Ainda 200: recebemos a notificação e a processamos (não é um
            # erro nosso nem algo que uma nova tentativa da InfinitePay
            # resolveria sozinho) — só que ela não bateu com o que
            # esperávamos, então o pedido continua "novo" em vez de virar
            # "confirmado".
            return Response({"success": True})

        pedido.status = "confirmado"
        pedido.save(update_fields=["status"])
        return Response({"success": True})

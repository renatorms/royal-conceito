import logging

from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido
from .permissions import IsDonorOrStaff, IsItemDonorOrStaff
from .serializers import (
    EnderecoSerializer,
    FreteCalcularSerializer,
    ItemPedidoSerializer,
    PedidoSerializer,
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
        endereco = serializer.validated_data.get("endereco")
        user = self.request.user
        if endereco and not user.is_staff and endereco.usuario != user:
            raise PermissionDenied("Você não pode vincular a este pedido um endereço que não é seu.")

        # Optional atomic path: POST /pedidos/ with an `itens_criacao` list
        # creates the Pedido and every ItemPedido line in a single DB
        # transaction. Popped out of validated_data before serializer.save()
        # because it isn't a real Pedido field — PedidoSerializer.create()
        # (ModelSerializer's default) would otherwise pass it straight to
        # Pedido.objects.create(**validated_data) and blow up on an
        # unexpected keyword argument.
        itens_data = serializer.validated_data.pop("itens_criacao", [])

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
            # instance — so this call is redundant whenever itens_data is
            # non-empty. It's not redundant when frete_selecionado was sent
            # but itens_criacao wasn't (an empty-Pedido-with-freight
            # request): no ItemPedido is created, so no signal ever fires,
            # and total would otherwise stay at 0 despite frete_valor being
            # set. Cheap and idempotent either way.
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

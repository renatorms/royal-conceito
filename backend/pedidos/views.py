from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from produtos.models import Variacao

from .models import Endereco, ItemPedido, Pedido
from .permissions import IsDonorOrStaff, IsItemDonorOrStaff
from .serializers import EnderecoSerializer, ItemPedidoSerializer, PedidoSerializer


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

        variacao = serializer.validated_data["variacao"]
        quantidade = serializer.validated_data["quantidade"]

        # Authoritative check: ATOMIC_REQUESTS is off, so an ItemPedido INSERT
        # commits immediately on .save(), before the post_save signal (and
        # its own separate @transaction.atomic block) even runs — raising
        # ValidationError from within the signal returns a clean 400, but the
        # invalid row itself is already committed by then (orphaned, never
        # reflected in Pedido.total since diminui_estoque's exception stops
        # atualiza_total_pedido from running). Checking here, before
        # serializer.save() is ever called, prevents the row from being
        # created at all. The signal's own check stays in place as a
        # defense-in-depth backstop for creation paths that don't go through
        # this view (e.g. the Django admin's ItemPedidoInline).
        if variacao.estoque < quantidade:
            raise ValidationError(
                {"detail": f"Estoque insuficiente. Restam apenas {variacao.estoque} unidades."}
            )

        serializer.save(preco_unitario=variacao.produto.preco)


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

        with transaction.atomic():
            serializer.save(usuario=self.request.user)
            pedido = serializer.instance

            for item in itens_data:
                # Re-fetch rather than trust the PrimaryKeyRelatedField
                # instance from validated_data: that was resolved once,
                # up front, when the whole payload was validated. If the
                # same variacao appears twice in itens_criacao, the second
                # occurrence must see the first occurrence's decrement
                # (applied a few lines below, inside this same transaction)
                # — not the pre-request stock level.
                variacao = Variacao.objects.get(pk=item["variacao"].pk)
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

                ItemPedido.objects.create(
                    pedido=pedido,
                    variacao=variacao,
                    quantidade=quantidade,
                    preco_unitario=variacao.produto.preco,
                )

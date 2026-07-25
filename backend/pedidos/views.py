from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

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

        serializer.save(usuario=self.request.user)

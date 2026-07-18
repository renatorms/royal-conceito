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
        serializer.save(usuario=self.request.user)

from django.contrib.auth.models import User
from django.db import models
from produtos.models import Variacao


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("novo", "Novo"),
        ("confirmado", "Confirmado"),
        ("enviado", "Enviado"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    cliente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="novo")

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    variacao = models.ForeignKey(Variacao, on_delete=models.PROTECT)
    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade}x - {self.variacao} - (Pedido #{self.pedido.id})"


class Endereco(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rua = models.CharField(max_length=100)
    numero = models.IntegerField()
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.cidade}/{self.estado}"

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import ItemPedido


@receiver(pre_save, sender=ItemPedido)
def calcula_subtotal(sender, instance, **kwargs):
    instance.subtotal = instance.quantidade * instance.preco_unitario


@receiver(post_save, sender=ItemPedido)
@transaction.atomic
def diminui_estoque(sender, instance, created, **kwargs):
    if created:
        variacao = instance.variacao

        # Valida se tem estoque suficiente
        if variacao.estoque < instance.quantidade:
            raise ValueError(
                f"Estoque insuficiente para {variacao.produto.nome} - {variacao.tamanho}! "
                f"Disponível: {variacao.estoque}, Solicitado: {instance.quantidade}"
            )

        variacao.estoque -= instance.quantidade
        variacao.save()


@receiver(post_save, sender=ItemPedido)
@transaction.atomic
def atualiza_total_pedido(
    sender, instance, **kwargs
):  # recalcula total de pedido automaticamente
    pedido = instance.pedido
    itens = pedido.itens.all()
    total = sum(item.subtotal for item in itens)
    pedido.total = total
    pedido.save()


@receiver(post_delete, sender=ItemPedido)
@transaction.atomic
def atualiza_total_ao_deletar(sender, instance, **kwargs):
    pedido = instance.pedido
    itens = pedido.itens.all()
    pedido.total = sum(item.subtotal for item in itens)
    pedido.save()

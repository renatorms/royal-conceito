from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ItemPedido


@receiver(post_save, sender=ItemPedido)
def diminui_estoque(sender, instance, created, **kwargs):
    if created:
        variacao = instance.variacao
        variacao.estoque -= instance.quantidade
        variacao.save()

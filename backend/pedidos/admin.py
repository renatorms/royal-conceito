from django.contrib import admin

from .models import Endereco, ItemPedido, Pedido

admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Endereco)
# Register your models here.

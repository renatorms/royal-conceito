from django.contrib import admin

from .models import ItemPedido, Pedido

admin.site.register(Pedido)
admin.site.register(ItemPedido)
# Register your models here.

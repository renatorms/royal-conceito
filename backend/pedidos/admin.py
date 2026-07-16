from django.contrib import admin

from .models import Endereco, ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["id", "usuario", "status", "total", "data_pedido"]
    list_filter = ["status", "data_pedido"]
    search_fields = ["usuario__username"]
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ["pedido", "variacao", "quantidade", "preco_unitario", "subtotal"]
    list_filter = ["pedido__status"]


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ["user", "rua", "cidade", "estado"]

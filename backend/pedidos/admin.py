from django.contrib import admin

from .models import Endereco, ItemPedido, Pedido

# preco_unitario/subtotal are always server-computed — preco_unitario from
# variacao.produto.preco (ItemPedidoViewSet.perform_create()), subtotal from
# the calcula_subtotal signal — and both are read_only on ItemPedidoSerializer,
# so the API never lets a client set them directly. Editable here would let a
# staff member silently drift an order's recorded price away from the real
# product price. Readonly only when editing an *existing* ItemPedido, not
# when creating one: preco_unitario has no default and isn't nullable at the
# DB level, so making it readonly on the add form too would leave no way to
# supply a value, and saving would fail with a NOT NULL constraint error.
ITEM_PEDIDO_CAMPOS_CALCULADOS = ["preco_unitario", "subtotal"]


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        # `obj` here is the *parent* Pedido, not the individual ItemPedido
        # row — Django applies one readonly_fields list to the whole inline
        # formset, not per-row. In practice a Pedido shown in this admin
        # always already exists (orders come from checkout, not from this
        # inline), so this reliably makes preco_unitario/subtotal readonly
        # for every existing line. The trade-off: it also makes them
        # readonly for any *new* row added via "Add another" on an existing
        # Pedido's page, since the formset can't tell old and new rows
        # apart — adding a line here would then hit the same NOT NULL
        # failure described above. Acceptable per the admin's actual use
        # (reviewing orders that already exist), not creating new ones.
        if obj is not None:
            return [*self.readonly_fields, *ITEM_PEDIDO_CAMPOS_CALCULADOS]
        return self.readonly_fields


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["id", "usuario", "status", "total", "data_pedido"]
    list_filter = ["status", "data_pedido"]
    search_fields = ["usuario__username"]
    inlines = [ItemPedidoInline]
    # Same reasoning as ITEM_PEDIDO_CAMPOS_CALCULADOS above — total is
    # always server-computed (the atualiza_total_pedido signal, as the sum
    # of ItemPedido.subtotal) and read_only on PedidoSerializer. Unlike
    # preco_unitario, this can be a plain unconditional readonly_fields
    # entry rather than get_readonly_fields(obj=None): Pedido.total has
    # default=0 (pedidos/models.py), so excluding it from the add form
    # doesn't risk a NOT NULL failure — a brand-new Pedido has no items
    # yet, so 0 is exactly the right value there too, not just a fallback.
    readonly_fields = ["total"]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ["pedido", "variacao", "quantidade", "preco_unitario", "subtotal"]
    list_filter = ["pedido__status"]

    def get_readonly_fields(self, request, obj=None):
        # Here `obj` is the specific ItemPedido being edited (this ModelAdmin
        # isn't an inline), so this cleanly means "existing item" vs.
        # "creating a new standalone ItemPedido" — see
        # ITEM_PEDIDO_CAMPOS_CALCULADOS above for why only the former is
        # readonly.
        if obj is not None:
            return [*self.readonly_fields, *ITEM_PEDIDO_CAMPOS_CALCULADOS]
        return self.readonly_fields


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "rua", "cidade", "estado"]

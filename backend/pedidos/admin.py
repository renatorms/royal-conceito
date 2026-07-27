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

# `quantidade` isn't server-computed like the fields above — a customer picks
# it at checkout, and it's normal (non-read_only) input on ItemPedidoSerializer
# and the itens_criacao entries on PedidoSerializer. The problem here is
# narrower: diminui_estoque (pedidos/signals.py) only validates/decrements
# stock `if created:` — editing quantidade on an *already-existing* ItemPedido
# changes it with no stock check and no corresponding Variacao.estoque
# adjustment at all, while calcula_subtotal/atualiza_total_pedido *do* rerun
# on every save, so subtotal/total silently recompute to match the new
# quantidade even though stock was never touched — a staff member could bump
# quantidade from 1 to 33 with zero validation and zero trace that stock
# wasn't checked. Same fix shape as ITEM_PEDIDO_CAMPOS_CALCULADOS (readonly
# only when obj is not None — quantidade has no default and isn't nullable,
# so making it readonly unconditionally would break creating a new item),
# confirmed with the user this isn't a workflow they rely on: any real
# quantity adjustment should go through the API/checkout, which validates
# stock correctly.
ITEM_PEDIDO_CAMPOS_SEM_VALIDACAO_NA_EDICAO = ["quantidade"]

# Same underlying problem as ITEM_PEDIDO_CAMPOS_SEM_VALIDACAO_NA_EDICAO above,
# for the two FKs instead of quantidade — found during the same admin audit
# but not fixed at the time (see CLAUDE.md). Reassigning `variacao` on an
# *existing* ItemPedido triggers no stock validation or adjustment at all:
# diminui_estoque only runs `if created:`, so neither the old variacao's
# stock is restored nor the new one is checked/decremented — the item ends
# up priced and accounted for a size that was never actually validated for
# this sale. Reassigning `pedido` moves the line to a different order, but
# atualiza_total_pedido only recalculates `instance.pedido` (the *new*
# order) on save — the *old* order's total is left stale, still counting a
# line that isn't its own anymore. Same fix, same conditional: readonly only
# when obj is not None, since neither FK has a default and both are
# required, so an unconditional readonly would break creating a new item.
# Any real reassignment should go through the API instead (cancel/recreate
# the item), which validates stock and keeps both orders' totals correct.
ITEM_PEDIDO_CAMPOS_FK_SEM_VALIDACAO_NA_EDICAO = ["pedido", "variacao"]


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        # `obj` here is the *parent* Pedido, not the individual ItemPedido
        # row — Django applies one readonly_fields list to the whole inline
        # formset, not per-row. In practice a Pedido shown in this admin
        # always already exists (orders come from checkout, not from this
        # inline), so this reliably makes these fields readonly for every
        # existing line. The trade-off: it also makes them readonly for any
        # *new* row added via "Add another" on an existing Pedido's page,
        # since the formset can't tell old and new rows apart — adding a
        # line here would then hit the same NOT NULL failure described
        # above. Acceptable per the admin's actual use (reviewing orders
        # that already exist), not creating new ones.
        if obj is not None:
            return [
                *self.readonly_fields,
                *ITEM_PEDIDO_CAMPOS_CALCULADOS,
                *ITEM_PEDIDO_CAMPOS_SEM_VALIDACAO_NA_EDICAO,
                *ITEM_PEDIDO_CAMPOS_FK_SEM_VALIDACAO_NA_EDICAO,
            ]
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
        # "creating a new standalone ItemPedido" — see the
        # ITEM_PEDIDO_CAMPOS_* constants above for why only the former is
        # readonly.
        if obj is not None:
            return [
                *self.readonly_fields,
                *ITEM_PEDIDO_CAMPOS_CALCULADOS,
                *ITEM_PEDIDO_CAMPOS_SEM_VALIDACAO_NA_EDICAO,
                *ITEM_PEDIDO_CAMPOS_FK_SEM_VALIDACAO_NA_EDICAO,
            ]
        return self.readonly_fields


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "rua", "cidade", "estado"]

    def get_readonly_fields(self, request, obj=None):
        # `usuario` is `read_only` on EnderecoSerializer — the fix for a real
        # IDOR (see CLAUDE.md, 24/07): without it, a PUT/PATCH to
        # /api/enderecos/{id}/ could reassign someone else's saved address to
        # the requester's own account, including its whole Pedido history via
        # Pedido.endereco. That fix only hardened the API — EnderecoAdmin had
        # no readonly_fields at all, so a staff member could do the exact
        # same reassignment through the admin's change form instead, same
        # hole, different door. Readonly only when editing an *existing*
        # Endereco (obj is not None), same as ItemPedido's fields above:
        # `usuario` has no default and isn't nullable
        # (models.ForeignKey(User, on_delete=models.CASCADE)), so making it
        # readonly unconditionally would break creating a new Endereco via
        # the admin (no way to supply a value, NOT NULL failure on save).
        if obj is not None:
            return [*self.readonly_fields, "usuario"]
        return self.readonly_fields

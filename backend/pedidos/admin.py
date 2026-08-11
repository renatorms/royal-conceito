from django import forms
from django.contrib import admin

from .models import Endereco, ItemPedido, Pedido, SolicitacaoTrocaDevolucao

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

# produto_nome/produto_tamanho are a different case from the fields above,
# deliberately *not* in ITEM_PEDIDO_CAMPOS_CALCULADOS: preco_unitario/
# subtotal must stay editable on the add form because nothing derives them
# automatically without extra code — but produto_nome/produto_tamanho are
# always supposed to be a direct copy of the chosen Variacao's own
# produto.nome/tamanho (see the ItemPedido model comment), never typed by
# hand, not even at creation. Free-typing them on the add form let a staff
# member pick Variacao "ADS COLOR - M" from the dropdown while typing
# "Camisa Teste" into produto_nome — a mismatch baked in at creation, not
# just an edit-time risk. So these are unconditionally readonly (see
# ItemPedidoAdmin.readonly_fields/ItemPedidoInline.readonly_fields below,
# not gated by obj is not None like every other conditional list in this
# file) — readonly_fields alone only stops typing, though, it doesn't
# *populate* the field for a new row, so ItemPedidoAdmin.save_model() and
# PedidoAdmin.save_formset() derive both from the instance's variacao
# directly, every time either is called (add or edit) — belt-and-suspenders
# against a forged payload as much as against a blank one, and idempotent
# on edit today since variacao is already readonly there too (see
# ITEM_PEDIDO_CAMPOS_FK_SEM_VALIDACAO_NA_EDICAO below), so re-deriving just
# re-asserts the same value that's already correctly stored.
ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS = ["produto_nome", "produto_tamanho"]

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


class ItemPedidoForm(forms.ModelForm):
    # Purely cosmetic, isolated from the data-integrity fix above: on the
    # *add* form, preco_unitario/subtotal are still editable — they only
    # become readonly_fields on edit (obj is not None) — so they still
    # render as the DecimalField default NumberInput there, spinner arrows
    # and all, which look bad on currency values. TextInput only changes
    # the rendering; Decimal validation still comes from the model field
    # itself (ItemPedido.preco_unitario/subtotal), untouched here. Has no
    # effect once a field is actually readonly: readonly_fields excludes it
    # from form.fields entirely, so no widget from this Meta is ever used
    # for it in that case — nothing to guard against here, Django already
    # handles it.
    class Meta:
        model = ItemPedido
        fields = "__all__"
        widgets = {
            "preco_unitario": forms.TextInput(),
            "subtotal": forms.TextInput(),
        }


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    form = ItemPedidoForm
    extra = 0
    # Unconditional — see ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS above for why
    # these two specifically aren't gated by obj is not None like the rest
    # of get_readonly_fields() below.
    readonly_fields = ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS

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
    # link_pagamento_url is included here too, also unconditionally: unlike
    # frete_valor/etc below (needed by hand for a phone order with no real
    # SuperFrete integration in the admin), there's no legitimate reason to
    # ever hand-type a payment link — it's a pure cache of what
    # PedidoViewSet.gerar_link_pagamento() got back from InfinitePay, always
    # either blank or that exact value. Safe unconditionally the same way
    # `total` is: the field is null=True, blank=True with no default, so
    # excluding it from the add form can't hit a NOT NULL failure either.
    readonly_fields = ["total", "link_pagamento_url"]

    def get_readonly_fields(self, request, obj=None):
        # usuario/endereco: same IDOR class as Endereco.usuario (see
        # CLAUDE.md, 24/07 and 27/07) — a staff member could otherwise
        # reassign an existing Pedido, and its whole item history, to a
        # different user directly through this change form, or link it to
        # another user's saved address with zero ownership validation.
        # Readonly only when editing an *existing* Pedido (obj is not None)
        # — unlike most of the other conditional fixes in this file, this
        # isn't forced by a NOT NULL constraint (both fields are
        # null=True, blank=True on the model): it's a deliberate choice,
        # per the user, to keep picking the customer/address a real part of
        # creating a Pedido by hand in the admin (e.g. a phone order), while
        # locking both down once the order exists.
        #
        # frete_valor/frete_nome/frete_transportadora/frete_prazo_dias: same
        # class of gap, found later (see CLAUDE.md) — these four are always
        # backend-set from frete_selecionado at checkout (read_only on
        # PedidoSerializer) and are meant to be a frozen snapshot of the
        # SuperFrete quote actually charged, same principle as
        # preco_unitario/produto_nome on ItemPedido. They were added later
        # (29/07, after this method already existed for usuario/endereco)
        # and simply never got folded into it, so a staff member could
        # rewrite a placed order's freight amount/carrier by hand with no
        # validation and no recalculation of total. Same conditional shape:
        # readonly only once the Pedido already exists, since there's no
        # real SuperFrete integration in the Admin to auto-fill them on
        # creation — a staff member building a phone order here has to be
        # able to type them in by hand.
        if obj is not None:
            return [
                *self.readonly_fields,
                "usuario",
                "endereco",
                "frete_valor",
                "frete_nome",
                "frete_transportadora",
                "frete_prazo_dias",
            ]
        return self.readonly_fields

    def save_formset(self, request, form, formset, change):
        # ItemPedidoInline is the only inline here. produto_nome/produto_
        # tamanho are unconditionally readonly on it (ITEM_PEDIDO_CAMPOS_
        # SEMPRE_DERIVADOS), so they can never be typed — but that alone
        # doesn't *populate* them for a brand-new ItemPedido added via "Add
        # another" on a Pedido's own *add* page, the one place this inline
        # still allows creating a new row at all (see ItemPedidoInline.
        # get_readonly_fields() above — on an existing Pedido, every field
        # is readonly, including variacao itself, so no new row can be
        # created there in the first place). Default save_formset() is just
        # `formset.save()`; derive both fields from each instance's variacao
        # before it's actually written, same as ItemPedidoAdmin.save_model()
        # below.
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            if obj.variacao_id:
                obj.produto_nome = obj.variacao.produto.nome
                obj.produto_tamanho = obj.variacao.tamanho
            obj.save()
        formset.save_m2m()


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    form = ItemPedidoForm
    list_display = ["pedido", "variacao", "quantidade", "preco_unitario", "subtotal"]
    list_filter = ["pedido__status"]
    # Unconditional — see ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS above.
    readonly_fields = ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS

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

    def save_model(self, request, obj, form, change):
        # readonly_fields keeps produto_nome/produto_tamanho from being
        # typed, but doesn't populate them — Django just excludes readonly
        # fields from the form entirely, leaving the model instance's
        # default (blank/None) untouched. Derive both from obj.variacao
        # here, unconditionally, whenever a variacao is set: this is what
        # actually fills them in on creation, and re-asserts them on every
        # edit save too (idempotent today, since variacao is already
        # readonly on edit — see ITEM_PEDIDO_CAMPOS_FK_SEM_VALIDACAO_NA_
        # EDICAO above — so this can't be re-deriving from a *different*
        # variacao than the one already on record). Mirrors how
        # ItemPedidoViewSet.perform_create() derives the same two fields
        # from variacao at the API level.
        if obj.variacao_id:
            obj.produto_nome = obj.variacao.produto.nome
            obj.produto_tamanho = obj.variacao.tamanho
        super().save_model(request, obj, form, change)


@admin.register(SolicitacaoTrocaDevolucao)
class SolicitacaoTrocaDevolucaoAdmin(admin.ModelAdmin):
    list_display = ["id", "item_pedido", "tipo", "status", "criado_em"]
    list_filter = ["tipo", "status"]
    search_fields = ["item_pedido__pedido__usuario__username", "item_pedido__produto_nome"]
    # `status` é o único campo pensado pra ser mudado por aqui — é onde a
    # API deixa a revisão da solicitação por enquanto (read_only na API, ver
    # SolicitacaoTrocaDevolucaoSerializer/CLAUDE.md). `item_pedido`/`tipo`/
    # `motivo` são o que o cliente efetivamente declarou ao abrir a
    # solicitação — mesmo espírito de ITEM_PEDIDO_CAMPOS_SEMPRE_DERIVADOS
    # acima (não deixar reescrever, por engano ou não, o que já foi
    # registrado), só que aqui é a submissão original do cliente sendo
    # protegida, não um valor derivado.
    readonly_fields = ["item_pedido", "tipo", "motivo", "criado_em", "atualizado_em"]


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

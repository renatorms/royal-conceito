from django.contrib import admin

from .models import Categoria, Marca, Produto, Variacao


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ["nome"]
    search_fields = ["nome"]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nome"]
    search_fields = ["nome"]


class VariacaoInline(admin.TabularInline):
    model = Variacao
    extra = 3
    fields = ["tamanho", "cor", "estoque", "peso", "altura", "largura", "comprimento"]
    # peso/altura/largura/comprimento (see the Variacao model comment) are
    # real, correctable measurements, not derived/protected data like
    # tamanho — no readonly concern for them, editable here on both existing
    # and new rows, same as estoque.
    # `produto` isn't in `fields` above, but that alone doesn't make it
    # readonly for an *existing* row — it's simply never shown here at all,
    # for any row, existing or new: Django's InlineModelAdmin auto-excludes
    # the FK-to-parent from the inline form regardless of `fields`, tying
    # every row to the parent Produto's own id structurally (confirmed via
    # curl — no `<select name="variacoes-0-produto">` ever renders, only a
    # hidden input). `tamanho`/`cor`, unlike `produto`, *are* real editable
    # fields here today, on both existing and new rows — same vulnerability
    # as VariacaoAdmin.get_readonly_fields() below, reachable through this
    # inline too. Readonly only when the *parent* Produto already exists
    # (obj is not None) — same trade-off already accepted for
    # ItemPedidoInline (pedidos/admin.py): once a Produto exists, "Add
    # another" on its own page also loses the ability to add a genuinely new
    # Variacao via this inline, since Django applies one readonly_fields
    # list to the whole formset, not per row. Adding a size/color to an
    # existing product should go through the standalone Variacao "Add" page
    # instead.
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [*self.readonly_fields, "tamanho", "cor"]
        return self.readonly_fields

    # Fixed 2026-08-01 — a real IntegrityError 500, not just a UX rough edge:
    # once `tamanho` became readonly above (obj is not None), the 3 blank
    # `extra` rows this inline still rendered on an *existing* Produto's page
    # became impossible to save correctly — a readonly field renders with no
    # <input>, so Django's ModelForm has no value to submit for it, and
    # trying to save one of those blank rows attempts to create a Variacao
    # with an empty tamanho. With more than one blank row present at once
    # (extra=3), several such rows collide with each other on
    # unique_together=["produto", "tamanho", "cor"] before the request even
    # reaches the DB-level NOT NULL/blank check, surfacing as an unhandled
    # 500 to a staff member who had no way of knowing those rows would never
    # actually work. get_readonly_fields() only ever locked existing rows
    # against being *edited* — it never addressed the inline still visually
    # offering to create new ones through a path that was silently broken by
    # that same fix. See get_extra()/has_add_permission() below for the fix,
    # and CLAUDE.md for the full incident writeup.
    def get_extra(self, request, obj=None, **kwargs):
        # No blank rows once the parent Produto already exists — there's
        # nothing for them to prefill successfully once tamanho is readonly,
        # so offering them at all is a guaranteed-to-fail invitation. On a
        # brand-new Produto, tamanho is still a real editable field (see
        # get_readonly_fields() above), so the normal extra=3 keeps making
        # sense there — pre-populating rows to create a product with a few
        # sizes in one go is the actual, working use case this inline exists
        # for in the first place.
        if obj is not None:
            return 0
        return super().get_extra(request, obj, **kwargs)

    def has_add_permission(self, request, obj):
        # Belt-and-suspenders with get_extra() above, not a redundant check:
        # get_extra()=0 removes the blank rows themselves, but Django's
        # inline template still renders a "+ Add another Variação" link
        # whenever this returns True (the link is what clones a fresh blank
        # row via JS) — without also disabling it here, staff would still
        # see a working-looking invitation to add a size that, per
        # get_readonly_fields() above, could never actually save correctly.
        # Creating a new size for an existing product still works — just
        # through the standalone Variacao "Add" page instead, which has none
        # of this inline's readonly restrictions.
        if obj is not None:
            return False
        return super().has_add_permission(request, obj)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["nome", "preco", "marca", "categoria", "em_outlet"]
    list_filter = ["categoria", "marca", "em_outlet"]
    search_fields = ["nome", "marca__nome"]
    # `imagem` (ImageField) já entra automaticamente como upload de arquivo
    # no formulário do Admin, sem precisar de nada explícito aqui — só
    # documentado porque é o ponto que substitui digitar imagem_url à mão
    # (ver produtos/models.py e docs/produtos.md). `criado_em` não aparece
    # no form (auto_now_add é sempre definido pelo Django, nunca editável).
    inlines = [VariacaoInline]


@admin.register(Variacao)
class VariacaoAdmin(admin.ModelAdmin):
    list_display = ["produto", "tamanho", "cor", "estoque"]
    list_filter = ["produto__categoria", "tamanho", "cor"]
    search_fields = ["produto__nome"]
    # peso/altura/largura/comprimento (see the Variacao model comment) are
    # visible/editable on the add/change form (not restricted here — this
    # ModelAdmin doesn't set `fields`, so every model field shows up there
    # by default), but deliberately not added to list_display/list_editable
    # alongside estoque: estoque is a live operational number that changes
    # with every sale/restock, so a fast, no-page-load edit from the
    # changelist genuinely matters; peso/dimensões are physical measurements
    # set once and rarely revisited — better suited to the full change form,
    # where all four show together with labels, than a cramped, easy-to-
    # fat-finger list-view cell for numbers that feed a real shipping-cost
    # calculation.
    list_editable = ["estoque"]

    def get_readonly_fields(self, request, obj=None):
        # produto/tamanho/cor identify *which* physical item this Variacao
        # is. Editing any of them on an existing Variacao doesn't just
        # affect future sales — ItemPedido now freezes its own
        # produto_nome/produto_tamanho at sale time (pedidos/models.py),
        # specifically so old orders can't be rewritten this way — but a
        # size that used to belong to product A silently starting to belong
        # to product B is still wrong on its own, and was the actual,
        # confirmed incident that prompted this fix (see CLAUDE.md): a real
        # R$1000 order for "ADS COLOR" started displaying as "Camisa Teste"
        # after its Variacao was reassigned. `cor` is locked here for the
        # same reason as `tamanho` — this project has no `ItemPedido.
        # produto_cor` snapshot yet (deliberately out of scope for the color
        # feature itself, see docs/produtos.md), so silently changing which
        # color an existing Variacao id represents would be invisible from
        # past orders too, not just current ones. Readonly only when editing
        # an existing Variacao (obj is not None): `produto`/`tamanho` have no
        # default, so an unconditional readonly would break creating a new
        # Variacao via the admin (no way to supply them, NOT NULL failure on
        # save) — `cor` does have a default ("Único") but is kept in this
        # same conditional for consistency, since it's part of the same
        # identity concern as tamanho, not an independent one.
        if obj is not None:
            return [*self.readonly_fields, "produto", "tamanho", "cor"]
        return self.readonly_fields

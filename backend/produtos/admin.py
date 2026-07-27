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
    fields = ["tamanho", "estoque", "peso", "altura", "largura", "comprimento"]
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
    # hidden input). `tamanho`, unlike `produto`, *is* a real editable field
    # here today, on both existing and new rows — same vulnerability as
    # VariacaoAdmin.get_readonly_fields() below, reachable through this
    # inline too. Readonly only when the *parent* Produto already exists
    # (obj is not None) — same trade-off already accepted for
    # ItemPedidoInline (pedidos/admin.py): once a Produto exists, "Add
    # another" on its own page also loses the ability to add a genuinely new
    # Variacao via this inline, since Django applies one readonly_fields
    # list to the whole formset, not per row. Adding a size to an existing
    # product should go through the standalone Variacao "Add" page instead.
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [*self.readonly_fields, "tamanho"]
        return self.readonly_fields


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["nome", "preco", "marca", "categoria"]
    list_filter = ["categoria", "marca"]
    search_fields = ["nome", "marca__nome"]
    inlines = [VariacaoInline]


@admin.register(Variacao)
class VariacaoAdmin(admin.ModelAdmin):
    list_display = ["produto", "tamanho", "estoque"]
    list_filter = ["produto__categoria", "tamanho"]
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
        # produto/tamanho identify *which* physical item this Variacao is.
        # Editing either on an existing Variacao doesn't just affect future
        # sales — ItemPedido now freezes its own produto_nome/produto_tamanho
        # at sale time (pedidos/models.py), specifically so old orders can't
        # be rewritten this way — but a size that used to belong to product A
        # silently starting to belong to product B is still wrong on its own,
        # and was the actual, confirmed incident that prompted this fix (see
        # CLAUDE.md): a real R$1000 order for "ADS COLOR" started displaying
        # as "Camisa Teste" after its Variacao was reassigned. Readonly only
        # when editing an existing Variacao (obj is not None): neither field
        # has a default, so an unconditional readonly would break creating a
        # new Variacao via the admin (no way to supply produto/tamanho, NOT
        # NULL failure on save).
        if obj is not None:
            return [*self.readonly_fields, "produto", "tamanho"]
        return self.readonly_fields

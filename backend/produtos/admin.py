from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse

from produtos.management.commands.seed_produtos import CATEGORIAS_CONFIG

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


class GerarVariacoesForm(forms.Form):
    # Formulário simples (não ModelForm) — não corresponde 1:1 a nenhum
    # model: `cor`/`estoque_inicial` são aplicados a várias Variacoes de
    # uma vez, e `tamanhos_padrao`/`tamanhos_extra` juntos formam a lista
    # real de tamanhos a criar, resolvida em GerarVariacoesForm.tamanhos()
    # abaixo, não um campo do model.
    cor = forms.CharField(max_length=50, label="Cor")
    tamanhos_padrao = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tamanhos padrão da categoria",
    )
    tamanhos_extra = forms.CharField(
        required=False,
        label="Tamanhos extras",
        help_text='Separados por vírgula, ex: "45,46" — para tamanhos fora do padrão da categoria.',
    )
    estoque_inicial = forms.IntegerField(min_value=0, initial=0, label="Estoque inicial")

    def __init__(self, *args, tamanhos_categoria=(), **kwargs):
        super().__init__(*args, **kwargs)
        # `choices`/`initial` construídos por instância, não na declaração
        # de classe acima — dependem da categoria do Produto sendo editado
        # (ver ProdutoAdmin.gerar_variacoes_view), que só se sabe em tempo
        # de request. Todos pré-marcados por padrão (requisito 2): `initial`
        # só é usado por um GET inicial — num POST reenviado após erro de
        # validação, o form já é bound e reflete o que o usuário realmente
        # marcou, não isto.
        self.fields["tamanhos_padrao"].choices = [(t, t) for t in tamanhos_categoria]
        self.fields["tamanhos_padrao"].initial = list(tamanhos_categoria)

    def clean(self):
        cleaned = super().clean()
        tamanhos_padrao = cleaned.get("tamanhos_padrao") or []
        tamanhos_extra_raw = cleaned.get("tamanhos_extra") or ""
        tamanhos_extra = [t.strip() for t in tamanhos_extra_raw.split(",") if t.strip()]
        if not tamanhos_padrao and not tamanhos_extra:
            raise forms.ValidationError(
                "Selecione ao menos um tamanho padrão ou informe um tamanho extra."
            )
        return cleaned

    def tamanhos(self):
        # dict.fromkeys: une os dois conjuntos preservando ordem e sem
        # duplicar um tamanho digitado em "extras" que também já estava
        # marcado nos checkboxes padrão.
        tamanhos_extra = [t.strip() for t in self.cleaned_data["tamanhos_extra"].split(",") if t.strip()]
        return list(dict.fromkeys([*self.cleaned_data["tamanhos_padrao"], *tamanhos_extra]))


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
    # `change_form_template` não é setado explicitamente aqui — o template
    # em produtos/templates/admin/produtos/produto/change_form.html já é
    # descoberto automaticamente pela busca padrão de templates do
    # ModelAdmin (admin/<app_label>/<model_name>/change_form.html), sem
    # precisar apontar pra ele. Esse template só acrescenta um botão
    # "Gerar variações em lote" ao object-tools existente (History/View on
    # site), visível apenas ao editar um Produto já salvo — ver
    # gerar_variacoes_view() abaixo e docs/produtos.md.

    def get_urls(self):
        urls = super().get_urls()
        # Antes de `urls` (não depois): mesma convenção da documentação do
        # Django pra ModelAdmin.get_urls() — não estritamente necessário
        # aqui (o sufixo "/gerar-variacoes/" não colide com nenhum path
        # padrão do Django admin, que usa sufixos fixos como "/change/"),
        # mas seguida por consistência/clareza.
        custom_urls = [
            path(
                "<int:produto_id>/gerar-variacoes/",
                self.admin_site.admin_view(self.gerar_variacoes_view),
                name="produtos_produto_gerar_variacoes",
            ),
        ]
        return custom_urls + urls

    def gerar_variacoes_view(self, request, produto_id):
        # self.admin_site.admin_view() (aplicado em get_urls() acima) já
        # exige request.user.is_active/is_staff antes mesmo desta view
        # rodar — mesma proteção de qualquer página do Admin, redireciona
        # pro login caso contrário. has_change_permission() abaixo é uma
        # segunda checagem, no nível do objeto específico, mesmo espírito
        # de qualquer view de change do próprio Django admin.
        produto = get_object_or_404(Produto, pk=produto_id)
        if not self.has_change_permission(request, produto):
            raise PermissionDenied

        tamanhos_categoria = []
        if produto.categoria is not None:
            config = CATEGORIAS_CONFIG.get(produto.categoria.nome)
            # Mesma regra de aplicar_variacoes_padrao.py: uma categoria fora
            # de CATEGORIAS_CONFIG simplesmente não tem tamanhos padrão pra
            # pré-marcar (checkboxes vazios) — o staff ainda pode usar
            # "Tamanhos extras" pra digitar os tamanhos à mão nesse caso,
            # nada trava.
            if config is not None:
                _tipos, _faixa_preco, tamanhos_categoria = config

        if request.method == "POST":
            form = GerarVariacoesForm(request.POST, tamanhos_categoria=tamanhos_categoria)
            if form.is_valid():
                cor = form.cleaned_data["cor"]
                estoque_inicial = form.cleaned_data["estoque_inicial"]

                criadas = 0
                puladas = 0
                for tamanho in form.tamanhos():
                    # get_or_create, não create direto: respeita
                    # unique_together=["produto", "tamanho", "cor"] sem
                    # estourar IntegrityError quando a combinação já existe
                    # — mesmo padrão de aplicar_variacoes_padrao.py. peso/
                    # altura/largura/comprimento ficam com o default do
                    # model (não pedidos neste formulário), editáveis depois
                    # individualmente se precisar de valor real.
                    _, criada = Variacao.objects.get_or_create(
                        produto=produto,
                        tamanho=tamanho,
                        cor=cor,
                        defaults={"estoque": estoque_inicial},
                    )
                    if criada:
                        criadas += 1
                    else:
                        puladas += 1

                self.message_user(
                    request,
                    f"{criadas} variação(ões) criada(s); {puladas} já existia(m) e "
                    "foram pulada(s).",
                    level=messages.SUCCESS,
                )
                return redirect(reverse("admin:produtos_produto_change", args=[produto.pk]))
        else:
            form = GerarVariacoesForm(tamanhos_categoria=tamanhos_categoria)

        context = {
            **self.admin_site.each_context(request),
            "title": f"Gerar variações em lote — {produto.nome}",
            "produto": produto,
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/produtos/produto/gerar_variacoes.html", context)


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

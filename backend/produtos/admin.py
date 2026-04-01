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
    fields = ["tamanho", "estoque"]


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
    list_editable = ["estoque"]

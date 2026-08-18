from rest_framework import serializers

from .models import (  # noqa: F401
    Categoria,
    Favorito,
    Marca,
    Produto,
    Variacao,
    chave_ordenacao_tamanho,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"


class VariacaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)

    class Meta:
        model = Variacao
        # peso/altura/largura/comprimento are writable (not read_only): these
        # are real physical measurements the client should be able to
        # correct once known, not something the backend derives — unlike
        # e.g. ItemPedido.preco_unitario. They currently ship with a
        # temporary placeholder default (see the Variacao model comment) for
        # the future SuperFrete shipping-cost integration; nothing consumes
        # them yet.
        fields = [
            "id",
            "produto",
            "produto_nome",
            "tamanho",
            "estoque",
            "peso",
            "altura",
            "largura",
            "comprimento",
        ]


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(
        source="categoria.nome", read_only=True, allow_null=True
    )
    # read_only=TRUE: só aparece na saída. SerializerMethodField, não
    # VariacaoSerializer(many=True, read_only=True) direto: precisa ordenar
    # a lista em Python antes de serializar (ver chave_ordenacao_tamanho()
    # em models.py) — sem isso, `variacoes` saía na ordem de inserção no
    # banco, não numérica/lógica (ex: "38" depois de "44" quando um tamanho
    # é cadastrado fora de sequência pelo Admin; ver CLAUDE.md). Chama
    # obj.variacoes.all() — reaproveita o cache de
    # ProdutoViewSet.get_queryset()'s prefetch_related("variacoes"), não
    # dispara uma query nova por produto.
    variacoes = serializers.SerializerMethodField()

    marca_nome = serializers.CharField(
        source="marca.nome", read_only=True, allow_null=True
    )

    def get_variacoes(self, obj):
        variacoes_ordenadas = sorted(
            obj.variacoes.all(), key=lambda v: chave_ordenacao_tamanho(v.tamanho)
        )
        return VariacaoSerializer(variacoes_ordenadas, many=True).data

    class Meta:
        model = Produto
        fields = [
            "id",
            "nome",
            "preco",
            "marca",
            "marca_nome",
            "categoria",
            "categoria_nome",
            "variacoes",
            "imagem",
            "imagem_url",
            "detalhes",
            "em_outlet",
            "criado_em",
        ]


class FavoritoSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
    # Nested ProdutoSerializer pro GET (mesmo produto sempre atual, não um
    # snapshot congelado — diferente de ItemPedido.produto_nome/
    # produto_tamanho, um Favorito não precisa sobreviver a uma edição
    # futura do produto com o dado antigo). `produto_id` é o contraponto de
    # escrita: PrimaryKeyRelatedField write_only, único jeito de o cliente
    # indicar qual produto favoritar, já que `produto` acima é read_only.
    produto_id = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(), source="produto", write_only=True
    )

    class Meta:
        model = Favorito
        # `usuario` não entra em fields — atribuído em
        # FavoritoViewSet.perform_create(), nunca aceito do cliente (mesma
        # proteção contra IDOR de EnderecoSerializer, só que aqui nem
        # exposto como read_only: não há nenhum caso de uso pra devolver o
        # dono no payload de um favorito).
        fields = ["id", "produto", "produto_id", "criado_em"]

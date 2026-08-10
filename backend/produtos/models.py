from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    marca = models.ForeignKey(
        Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name="produtos"
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="produtos"
    )
    # SET_NULL: deletar categoria não remove o produto do sistema
    imagem_url = models.CharField(max_length=255, null=True, blank=True)
    # CharField, não URLField: guarda um caminho relativo servido pelo próprio
    # frontend (ex: "/produtos/CONJUNTO-LACOSTE-2026.jpg", arquivo estático em
    # frontend/public/produtos/ — ver produtos/management/commands/
    # importar_produtos_reais.py e CLAUDE.md), não uma URL absoluta externa.
    # Confirmado que URLField/URLValidator rejeita esse formato (exige
    # esquema, ex. "https://") — usar URLField faria qualquer save() futuro
    # através de um ModelForm (ex: Django Admin) ou de um serializer que
    # valide o campo falhar com "Insira um URL válido.", mesmo o valor sendo
    # correto para como o app realmente serve a imagem. null=True/blank=True
    # porque um Produto pode existir sem imagem (ex: cadastrado à mão no
    # admin antes de uma foto real ser adicionada).

    def __str__(self):
        return self.nome


# Ordem lógica dos tamanhos de roupa — não alfabética por coincidência
# (P < M < G já bateria com ordem alfabética, mas GG/XG não: "GG" vem antes
# de "M" alfabeticamente, o que estaria errado). Mantida em sincronia manual
# com TAMANHOS_ROUPA em produtos/management/commands/seed_produtos.py — não
# importada de lá de propósito: aquele módulo é um management command
# (dependência opcional, só carregada quando o comando roda), enquanto
# chave_ordenacao_tamanho() abaixo é código de request/serialização, chamado
# em todo GET /produtos/ — não deveria depender de um comando de management
# para funcionar. Se um novo tamanho de roupa for adicionado em um dos dois
# lugares, adicionar no outro também.
ORDEM_TAMANHOS_ROUPA = ["P", "M", "G", "GG", "XG"]


def chave_ordenacao_tamanho(tamanho):
    """Chave de ordenação lógica (não alfabética) para Variacao.tamanho.

    tamanho é um CharField de texto livre, não um IntegerField. Antes desta
    função, ProdutoSerializer/ProdutoViewSet não aplicavam NENHUMA ordenação
    a `variacoes` — nem numérica nem alfabética — então a ordem exibida era
    simplesmente a ordem de inserção no banco (a ordem em que cada Variacao
    foi criada). Isso funciona por acaso enquanto os tamanhos são cadastrados
    em sequência crescente (import_produtos_reais.py/aplicar_variacoes_
    padrao.py fazem isso), mas quebra assim que um tamanho é adicionado
    depois dos demais pelo Django Admin (ex: reposição de um tamanho que
    faltava) — foi exatamente esse o bug real observado, não uma ordenação
    alfabética explícita (ver CLAUDE.md). Três grupos, cada um ordenado
    corretamente dentro de si e nunca misturado entre si (um Produto na
    prática só tem tamanhos de um grupo, mas a função não assume isso):
      1. Puramente numérico (calçado, ex: "38") -> ordena pelo valor inteiro.
      2. Tamanho de roupa reconhecido (ver ORDEM_TAMANHOS_ROUPA) -> ordena
         pela posição na lista.
      3. Qualquer outro valor (tamanho único "U", ou algo inesperado) ->
         ordena por último, alfabeticamente entre si.
    """
    if tamanho.isdigit():
        return (0, int(tamanho), "")
    if tamanho in ORDEM_TAMANHOS_ROUPA:
        return (1, ORDEM_TAMANHOS_ROUPA.index(tamanho), "")
    return (2, 0, tamanho)


class Variacao(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="variacoes"
    )
    # CASCADE: variação não existe sem produto
    tamanho = models.CharField(max_length=3)
    estoque = models.IntegerField(default=0)
    peso = models.DecimalField(max_digits=5, decimal_places=3, default=0.3)
    altura = models.IntegerField(default=3)
    largura = models.IntegerField(default=25)
    comprimento = models.IntegerField(default=35)
    # peso (kg) / altura, largura, comprimento (cm) — necessários para a
    # futura integração com o cálculo de frete da SuperFrete (ver
    # CLAUDE.md). Cadastrados por Variacao, não por Produto: mesmo padrão
    # de mercado usado por Nuvemshop/Shopify — permite precisão quando
    # necessário (uma variação P e uma XG do mesmo produto podem pesar/medir
    # diferente), mesmo que na prática a maioria das variações de um mesmo
    # produto acabe usando valores parecidos. altura/largura/comprimento
    # são IntegerField, não DecimalField: embalagem de frete normalmente é
    # medida/declarada em cm inteiros (mesma convenção usada por
    # Correios/Melhor Envio/SuperFrete), sem necessidade real de precisão
    # sub-centimétrica; peso usa DecimalField(decimal_places=3) porque
    # gramas fazem diferença real no cálculo de frete. default, não
    # null=True: frete sempre precisa de algum valor pra calcular, então um
    # valor aproximado é melhor que ausência de dado. Os padrões
    # (0.3kg, 3×25×35cm) são um envelope/pacote típico pra roupa dobrada —
    # placeholder temporário até o cliente confirmar os valores reais por
    # produto; nenhuma Variacao existente no banco tinha esse dado antes
    # desta migration, então todas ficam com esse valor aproximado até
    # serem ajustadas manualmente no admin.

    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"
        unique_together = ["produto", "tamanho"]

    def __str__(self):
        return f"{self.produto.nome} - {self.tamanho}"

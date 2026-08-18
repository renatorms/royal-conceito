import re

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
    imagem = models.ImageField(upload_to="produtos/", null=True, blank=True)
    # Adicionado junto com MEDIA_ROOT/MEDIA_URL (core/settings.py) para
    # permitir upload real de arquivo pelo Django Admin, em vez de exigir
    # digitar um caminho/URL à mão em imagem_url. Convivem os dois campos:
    # imagem_url continua sendo a fonte pros ~115 produtos já importados via
    # importar_produtos_reais.py (caminho relativo servido pelo frontend);
    # imagem é preenchido só para produtos cadastrados/editados dali em
    # diante pelo Admin. ProdutoSerializer/frontend priorizam imagem quando
    # presente, com fallback pra imagem_url. Solução intermediária: storage
    # local do Django (MEDIA_ROOT) não é produção-ready (mesma pendência de
    # sempre sobre hospedagem real de imagem — ver CLAUDE.md/docs/produtos.md).
    detalhes = models.TextField(blank=True)
    # Texto livre, opcional, editável pelo Admin — descrição/ficha técnica do
    # produto exibida na página de detalhe (frontend). blank=True (não
    # null=True): TextField vazio já é representado por "" no banco, sem
    # necessidade de um terceiro estado NULL; o frontend usa a string vazia
    # pra decidir não renderizar a seção "Detalhes do produto".
    em_outlet = models.BooleanField(default=False)
    # Sem modelo de desconto/preço promocional — só marca visibilidade no
    # link direto "Outlet" do Header (HeaderNav.jsx, /?em_outlet=true).
    # default=False: nenhum produto existente vira outlet automaticamente,
    # marcação é manual pelo Admin.
    criado_em = models.DateTimeField(auto_now_add=True)
    # auto_now_add: todo Produto já existente no banco recebeu a data da
    # migration como criado_em (não a data real de cadastro, que não era
    # guardada até agora) — limitação documentada, não um bug; só produtos
    # criados a partir desta migration têm um criado_em fiel. Usado pela
    # ordenação "Mais recentes" do Catálogo (ProdutoViewSet.ordering_fields).

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

# Reconhece uma faixa "NN-NN" (ex: "35-40", tamanho de meia — ver
# TAMANHOS_MEIA em produtos/management/commands/seed_produtos.py). Só dois
# grupos de dígitos separados por um hífen — não usa `\d+` sozinho porque
# isso também casaria parcialmente algo como "35-" ou "-40"; `$`/`^` (via
# fullmatch) garantem que a string inteira é a faixa, nada sobrando.
PADRAO_FAIXA_TAMANHO = re.compile(r"(\d+)-(\d+)")


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
    alfabética explícita (ver CLAUDE.md). Quatro grupos, cada um ordenado
    corretamente dentro de si e nunca misturado entre si (um Produto na
    prática só tem tamanhos de um grupo, mas a função não assume isso):
      1. Puramente numérico (calçado, ex: "38") -> ordena pelo valor inteiro.
      2. Faixa "NN-NN" (meia, ex: "35-40" — ver PADRAO_FAIXA_TAMANHO acima)
         -> ordena pelo primeiro número da faixa. Checado ANTES do grupo de
         roupa abaixo (a ordem dos `if`s importa: uma faixa não bate em
         `isdigit()` por causa do hífen, então só precisa vir antes de
         cair no catch-all por eliminação).
      3. Tamanho de roupa reconhecido (ver ORDEM_TAMANHOS_ROUPA) -> ordena
         pela posição na lista.
      4. Qualquer outro valor (tamanho único "U", ou algo inesperado) ->
         ordena por último, alfabeticamente entre si.
    """
    if tamanho.isdigit():
        return (0, int(tamanho), "")
    faixa = PADRAO_FAIXA_TAMANHO.fullmatch(tamanho)
    if faixa:
        return (1, int(faixa.group(1)), "")
    if tamanho in ORDEM_TAMANHOS_ROUPA:
        return (2, ORDEM_TAMANHOS_ROUPA.index(tamanho), "")
    return (3, 0, tamanho)


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

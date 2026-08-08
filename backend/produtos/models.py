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

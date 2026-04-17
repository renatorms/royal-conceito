from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

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
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    # SET_NULL: deletar categoria não remove o produto do sistema

    def __str__(self):
        return self.nome


class Variacao(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="variacoes"
    )
    # CASCADE: variação não existe sem produto
    tamanho = models.CharField(max_length=3)
    estoque = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"
        unique_together = ["produto", "tamanho"]

    def __str__(self):
        return f"{self.produto.nome} - {self.tamanho}"

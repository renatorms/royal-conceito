from django.db import models  # importas a biblioteca de modelos do Django


class Categoria(
    models.Model
):  # criamos uma classe Categoria que herda modelos da classe Model do Django
    nome = models.CharField(
        max_length=100
    )  # definição de um campo de texto para o nome da categoria com tamanho máximo de 100 caracteres

    def __str__(self):
        return self.nome
        # método __str__ para retornar o nome da categoria como representação em string


class Produto(
    models.Model
):  # criamos uma classe Produto que herda modelos da classe Model do Django
    nome = models.CharField(
        max_length=100
    )  # produto com tamanho máximo de 100 caracteres
    preco = models.DecimalField(
        max_digits=10, decimal_places=2
    )  #  preço do produto, com até 10 dígitos no total e 2 casas decimais
    marca = models.CharField(
        max_length=50, default="Sem marca", blank=True
    )  # definição de um campo de texto para a marca do produto com tamanho máximo de 50 caracteres
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    # SET_NULL: deletar categoria não remove o produto do sistema

    def __str__(self):
        return (
            self.nome
        )  # método __str__ para retornar o nome do produto como representação em string


class Variacao(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE
    )  # deleta categoria e todos os produtos
    tamanho = models.CharField(max_length=3)
    estoque = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Variação"
        verbose_name_plural = "Variações"

    def __str__(self):
        return f"{self.produto.nome} - {self.tamanho}"

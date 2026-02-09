from django.db import models  # importas a biblioteca de modelos do Django


class Produto(
    models.Model
):  # criamos uma classe Produto que herda modelos da classe Model do Django
    nome = models.CharField(
        max_length=100
    )  # definimos um campo de texto para o nome do produto com tamanho máximo de 100 caracteres
    preco = models.DecimalField(
        max_digits=10, decimal_places=2
    )  #  definição de um campo decimal para o preço do produto, com até 10 dígitos no total e 2 casas decimais
    estoque = models.IntegerField(
        default=0
    )  # Definição de um campo inteiro para a quantidade em estoque do produto, com valor padrão de 0
    marca = models.CharField(
        max_length=50
    )  # definição de um campo de texto para a marca do produto com tamnho máximo de 50 caracteres

    def __str__(self):
        return (
            self.nome
        )  # método __str__ para retornar o nome do produto como representação em string

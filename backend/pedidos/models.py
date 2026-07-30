from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from produtos.models import Variacao


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("novo", "Novo"),
        ("confirmado", "Confirmado"),
        ("enviado", "Enviado"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    endereco = models.ForeignKey(
        "Endereco",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    # PROTECT: um pedido histórico não pode perder a referência de para onde
    # foi enviado — não deixa deletar um endereço vinculado a algum pedido
    # (mesmo padrão de ItemPedido.variacao abaixo, que não deixa deletar uma
    # variação vendida)
    data_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="novo")
    frete_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frete_nome = models.CharField(max_length=50, null=True, blank=True)
    frete_transportadora = models.CharField(max_length=100, null=True, blank=True)
    frete_prazo_dias = models.IntegerField(null=True, blank=True)
    # Snapshot da opção de frete escolhida no checkout — congelado uma única
    # vez na criação do Pedido (mesmo espírito de ItemPedido.preco_unitario/
    # produto_nome, ver CLAUDE.md), nunca recalculado depois, mesmo que a
    # cotação da SuperFrete para o mesmo destino mude no futuro. null=True,
    # blank=True: pedidos de antes desta mudança (incluindo os que usavam o
    # FRETE_PLACEHOLDER fixo do frontend) não têm cotação real nenhuma pra
    # guardar, e não são preenchidos retroativamente com um valor adivinhado
    # — mesmo princípio já usado em ItemPedido.produto_nome/produto_tamanho.
    # `total` passa a incluir frete_valor quando presente (ver
    # signals.py::recalcula_total_pedido) — pedidos antigos, com
    # frete_valor=None, continuam com total = soma dos itens, sem mudança de
    # comportamento.

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    # CASCADE: se deletar pedido, deleta itens
    variacao = models.ForeignKey(Variacao, on_delete=models.PROTECT)
    # PROTECT: não deixa deletar variação se foi vendida
    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    produto_nome = models.CharField(max_length=100, null=True, blank=True)
    produto_tamanho = models.CharField(max_length=3, null=True, blank=True)
    # produto_nome/produto_tamanho are a snapshot, frozen once at creation
    # (same spirit as preco_unitario) — not derived from `variacao` on every
    # read. Variacao.produto and Variacao.tamanho can both be edited later
    # (product reassigned, size relabeled), and before this fix ItemPedido
    # had no columns of its own for either — ItemPedidoSerializer exposed
    # them via source="variacao.produto.nome"/source="variacao.tamanho",
    # so editing an old Variacao silently rewrote what every past order
    # that ever sold it appeared to contain, even though the actual sale
    # never changed. null=True, blank=True because this is a new column on
    # an existing table — no migration can know what a pre-existing
    # ItemPedido's product/size actually were at the time of that sale, and
    # guessing via the *current* Variacao would just reintroduce the same
    # bug for historical rows instead of fixing it. See CLAUDE.md for the
    # full incident.

    def __str__(self):
        return f"{self.quantidade}x - {self.variacao} - (Pedido #{self.pedido.id})"


class Endereco(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    # CASCADE: se deletar usuário, deleta endereços
    rua = models.CharField(max_length=100)
    numero = models.IntegerField()
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.cidade}/{self.estado}"

from django.core.management.base import BaseCommand

from produtos.models import Produto

# Produto [91] "Bonés Variados" (categoria Bonés, TAMANHO_UNICO) tinha uma
# Variacao com tamanho="s/n" em vez de "U" — fora do padrão que toda outra
# Variacao de categoria TAMANHO_UNICO usa neste projeto (Relógios, Óculos,
# Carteiras, Outros Acessórios, Shoulder Bag, ...). Encontrado ao investigar
# a separação do produto Oakley combinado; corrigido aqui, isolado, para não
# misturar uma correção de dado com aquele split — ver CLAUDE.md.
ID_PRODUTO = 91
TAMANHO_ERRADO = "s/n"
TAMANHO_CORRETO = "U"


class Command(BaseCommand):
    help = (
        "Corrige a Variacao do Produto [91] 'Bonés Variados' de "
        f"tamanho={TAMANHO_ERRADO!r} para tamanho={TAMANHO_CORRETO!r} "
        "(o padrão real de toda categoria TAMANHO_UNICO neste projeto), "
        "preservando o estoque atual sem alteração. Idempotente: se a "
        "Variacao já estiver com o tamanho correto, não faz nada."
    )

    def handle(self, *args, **options):
        try:
            produto = Produto.objects.prefetch_related("variacoes").get(id=ID_PRODUTO)
        except Produto.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Produto id {ID_PRODUTO} não encontrado."))
            return

        variacao = produto.variacoes.filter(tamanho=TAMANHO_ERRADO).first()
        if variacao is None:
            ja_correta = produto.variacoes.filter(tamanho=TAMANHO_CORRETO).exists()
            if ja_correta:
                self.stdout.write(
                    f"[{produto.id}] {produto.nome!r}: já tem uma Variacao com "
                    f"tamanho={TAMANHO_CORRETO!r} — nada a fazer."
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{produto.id}] {produto.nome!r}: nenhuma Variacao com "
                        f"tamanho={TAMANHO_ERRADO!r} encontrada, e nenhuma com "
                        f"{TAMANHO_CORRETO!r} tampouco — estado inesperado, nada alterado."
                    )
                )
            return

        self.stdout.write(
            f"[{produto.id}] {produto.nome!r}: Variacao id {variacao.id}, "
            f"tamanho={variacao.tamanho!r}, estoque={variacao.estoque} (antes)"
        )
        variacao.tamanho = TAMANHO_CORRETO
        variacao.save(update_fields=["tamanho"])
        self.stdout.write(
            f"[{produto.id}] {produto.nome!r}: Variacao id {variacao.id}, "
            f"tamanho={variacao.tamanho!r}, estoque={variacao.estoque} (depois)"
        )

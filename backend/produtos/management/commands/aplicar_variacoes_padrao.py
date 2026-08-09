from django.core.management.base import BaseCommand

from produtos.management.commands.seed_produtos import CATEGORIAS_CONFIG
from produtos.models import Produto, Variacao

ESTOQUE_PADRAO = 10


class Command(BaseCommand):
    help = (
        "Cria um conjunto de Variacao padrão (tamanhos da categoria + "
        f"estoque={ESTOQUE_PADRAO} cada) para todo Produto que já tem categoria "
        "definida mas ainda não tem nenhuma Variacao — o caso normal dos 116 "
        "produtos reais importados via importar_produtos_reais.py enquanto o "
        "usuário preenche categoria/marca/preço manualmente pelo Django Admin, "
        "aos poucos. Evita o trabalho repetitivo de criar cada tamanho na mão "
        "para produtos cuja tabela de tamanhos já é óbvia a partir da categoria. "
        "Reaproveita CATEGORIAS_CONFIG de seed_produtos.py em vez de duplicar essa "
        "tabela categoria->tamanhos uma terceira vez no backend — uma categoria só "
        "recebe variações automáticas se já estiver nesse mapeamento; qualquer "
        "outra é listada no final para decisão manual, nada é criado às cegas. "
        "Idempotente: como o filtro já exclui produtos que já têm alguma "
        "Variacao, rodar de novo não duplica nada."
    )

    def handle(self, *args, **options):
        candidatos = (
            Produto.objects.filter(categoria__isnull=False, variacoes__isnull=True)
            .select_related("categoria")
            .order_by("categoria__nome", "nome")
        )

        produtos_atualizados = 0
        variacoes_criadas = 0
        nao_reconhecidos = []

        for produto in candidatos:
            config = CATEGORIAS_CONFIG.get(produto.categoria.nome)
            if config is None:
                nao_reconhecidos.append(produto)
                continue

            _tipos, _faixa_preco, tabela_tamanhos = config
            for tamanho in tabela_tamanhos:
                _, criada = Variacao.objects.get_or_create(
                    produto=produto,
                    tamanho=tamanho,
                    defaults={"estoque": ESTOQUE_PADRAO},
                )
                if criada:
                    variacoes_criadas += 1
            produtos_atualizados += 1

        self.stdout.write(self.style.SUCCESS("Aplicação de variações padrão concluída."))
        self.stdout.write(f"Produtos que receberam variações: {produtos_atualizados}")
        self.stdout.write(f"Variações criadas no total: {variacoes_criadas}")

        if nao_reconhecidos:
            self.stdout.write(
                self.style.WARNING(
                    f"Produtos com categoria não reconhecida em CATEGORIAS_CONFIG "
                    f"(nada criado, decisão manual): {len(nao_reconhecidos)}"
                )
            )
            for produto in nao_reconhecidos:
                self.stdout.write(
                    f"  - [{produto.id}] {produto.nome!r} (categoria: {produto.categoria.nome!r})"
                )
        else:
            self.stdout.write("Nenhum produto com categoria não reconhecida.")

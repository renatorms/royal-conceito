import random

from django.core.management.base import BaseCommand, CommandError

from produtos.management.commands.aplicar_variacoes_padrao import ESTOQUE_PADRAO
from produtos.management.commands.seed_produtos import CATEGORIAS_CONFIG, gerar_preco
from produtos.models import Categoria, Marca, Produto, Variacao

# As 10 marcas que devem aparecer em TODA Categoria, garantindo que cada
# combinação categoria×marca exista no catálogo (necessário para que o
# Header — ver CategoriaMenuView/HeaderNav.jsx no CLAUDE.md — tenha algo
# para mostrar em cada cruzamento). Chaveado por id, com o nome esperado ao
# lado como checagem de sanidade (ver _resolver_marcas_alvo abaixo): se o
# nome real no banco não bater com o valor aqui, o comando aborta sem criar
# nada, em vez de silenciosamente vincular produtos à marca errada.
#
# id 47: o nome real cadastrado no banco é "Louis Vuiton" (sem o segundo
# "t" de "Vuitton") — confirmado via shell ao construir este comando; é a
# única marca "Louis Vuit(t)on" cadastrada, então claramente é a pretendida,
# só com um typo no cadastro original. Usa-se aqui a grafia real do banco
# deliberadamente (decisão do usuário) em vez de corrigir o cadastro da
# Marca como parte deste comando — os dois são tarefas independentes.
MARCAS_ALVO_IDS = {
    48: "Armani",
    54: "Balenciaga",
    35: "Boss",
    51: "Casa Blanca",
    53: "Diesel",
    50: "Gucci",
    34: "Lacoste",
    47: "Louis Vuiton",
    32: "Nike",
    52: "Zara",
}

# Faixa de preço usada quando a Categoria não está mapeada em
# CATEGORIAS_CONFIG (seed_produtos.py) — mesmo fallback conservador que
# aplicar_variacoes_padrao.py já aplica para variações (ver abaixo): nada é
# inventado para uma categoria desconhecida além de um preço plausível.
PRECO_FAIXA_GENERICA = (100, 500)

# Semente própria (não a de seed_produtos.py) — só precisa ser determinística
# dentro de uma execução, não coordenada com o gerador de fixtures.
SEED = 4750

PREFIXO_NOME_TESTE = "[TESTE]"


class Command(BaseCommand):
    help = (
        "Garante que as 10 marcas listadas em MARCAS_ALVO_IDS estejam "
        "representadas (produto com categoria+marca definidas e pelo menos "
        "uma Variacao) em toda Categoria já cadastrada — cria um Produto de "
        "teste, com nome prefixado '[TESTE]', para cada combinação "
        "categoria×marca ainda faltante, junto com suas Variacoes padrão "
        "(mesma tabela de tamanhos de aplicar_variacoes_padrao.py). Existe "
        "só para garantir cobertura de navegação no Header durante "
        "desenvolvimento/demonstração — os produtos criados são fixture de "
        "teste, não catálogo real, e devem ser removidos antes de produção "
        "(filtrar por Produto.objects.filter(nome__startswith='[TESTE]')). "
        "Idempotente: uma combinação categoria×marca já coberta (por este "
        "comando numa execução anterior, ou por um produto cadastrado à mão "
        "pelo usuário) nunca gera um novo produto."
    )

    def handle(self, *args, **options):
        marcas_alvo = self._resolver_marcas_alvo()
        rng = random.Random(SEED)

        total_produtos_criados = 0
        total_variacoes_criadas = 0
        total_ja_cobertas = 0
        total_criadas_agora = 0
        categorias_sem_variacao = []

        categorias = list(Categoria.objects.order_by("nome"))
        if not categorias:
            self.stdout.write(self.style.WARNING("Nenhuma Categoria cadastrada. Nada a fazer."))
            return

        for categoria in categorias:
            config = CATEGORIAS_CONFIG.get(categoria.nome)
            ja_cobertas = 0
            criadas_agora = 0
            produtos_criados_categoria = 0
            variacoes_criadas_categoria = 0

            for marca in marcas_alvo:
                coberta = Produto.objects.filter(
                    categoria=categoria, marca=marca, variacoes__isnull=False
                ).exists()
                if coberta:
                    ja_cobertas += 1
                    continue

                criadas_agora += 1
                nome_produto = f"{PREFIXO_NOME_TESTE} {categoria.nome} {marca.nome}"
                faixa_preco = config[1] if config is not None else PRECO_FAIXA_GENERICA
                preco = gerar_preco(faixa_preco, rng)

                # get_or_create por nome (não .create()) — resume de forma
                # idempotente mesmo se uma execução anterior tiver criado o
                # Produto e sido interrompida antes de gerar as Variacoes:
                # `coberta` acima só é True quando já existe alguma
                # Variacao, então um Produto "órfão" desse tipo seria
                # recriado (duplicado) por um .create() simples.
                produto, produto_criado = Produto.objects.get_or_create(
                    nome=nome_produto,
                    defaults={
                        "preco": preco,
                        "categoria": categoria,
                        "marca": marca,
                    },
                )
                if produto_criado:
                    produtos_criados_categoria += 1
                    total_produtos_criados += 1

                if config is not None:
                    _tipos, _faixa, tabela_tamanhos = config
                    for tamanho in tabela_tamanhos:
                        _, variacao_criada = Variacao.objects.get_or_create(
                            produto=produto,
                            tamanho=tamanho,
                            defaults={"estoque": ESTOQUE_PADRAO},
                        )
                        if variacao_criada:
                            variacoes_criadas_categoria += 1
                            total_variacoes_criadas += 1
                else:
                    categorias_sem_variacao.append((categoria, marca, produto))

            total_ja_cobertas += ja_cobertas
            total_criadas_agora += criadas_agora

            self.stdout.write(
                f"[{categoria.nome}] já cobertas: {ja_cobertas} | "
                f"criadas agora: {criadas_agora} | "
                f"produtos criados: {produtos_criados_categoria} | "
                f"variações criadas: {variacoes_criadas_categoria}"
            )

        self.stdout.write(self.style.SUCCESS("Cobertura de marcas por categoria concluída."))
        self.stdout.write(f"Categorias processadas: {len(categorias)}")
        self.stdout.write(f"Combinações categoria×marca já cobertas: {total_ja_cobertas}")
        self.stdout.write(f"Combinações categoria×marca criadas agora: {total_criadas_agora}")
        self.stdout.write(f"Produtos de teste criados: {total_produtos_criados}")
        self.stdout.write(f"Variações criadas: {total_variacoes_criadas}")

        if categorias_sem_variacao:
            self.stdout.write(
                self.style.WARNING(
                    "Categorias sem entrada em CATEGORIAS_CONFIG — produto de "
                    "teste criado, mas SEM Variacao (não fica comprável até "
                    "alguém definir a tabela de tamanhos manualmente, mesma "
                    f"regra de aplicar_variacoes_padrao.py): {len(categorias_sem_variacao)}"
                )
            )
            for categoria, marca, produto in categorias_sem_variacao:
                self.stdout.write(
                    f"  - [{produto.id}] {produto.nome!r} "
                    f"(categoria: {categoria.nome!r}, marca: {marca.nome!r})"
                )

    def _resolver_marcas_alvo(self):
        marcas_por_id = {m.id: m for m in Marca.objects.filter(id__in=MARCAS_ALVO_IDS)}

        faltando = set(MARCAS_ALVO_IDS) - set(marcas_por_id)
        if faltando:
            raise CommandError(
                f"Marca(s) com id {sorted(faltando)} não encontrada(s) no banco. "
                "Nada foi criado — confira MARCAS_ALVO_IDS antes de rodar de novo."
            )

        divergentes = [
            (id_, nome_esperado, marcas_por_id[id_].nome)
            for id_, nome_esperado in MARCAS_ALVO_IDS.items()
            if marcas_por_id[id_].nome != nome_esperado
        ]
        if divergentes:
            detalhes = "; ".join(
                f"id {id_}: esperado {esperado!r}, encontrado {real!r}"
                for id_, esperado, real in divergentes
            )
            raise CommandError(
                f"Nome de marca não bate com MARCAS_ALVO_IDS ({detalhes}). "
                "Nada foi criado — confira o id/nome antes de rodar de novo."
            )

        return [marcas_por_id[id_] for id_ in MARCAS_ALVO_IDS]

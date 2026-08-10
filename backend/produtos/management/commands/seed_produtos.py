import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from produtos.models import Categoria, Marca, Produto, Variacao

# Reused if already present in the DB (by `nome`, via get_or_create), added
# otherwise — never duplicated. Real streetwear/grife brand names, matching
# what the real catalog already uses (Nike, Lacoste, Boss, Oakley, ...): this
# is fixture data for a legitimate multi-brand resale storefront, the same
# business model the real store already runs.
MARCAS = [
    "Nike", "Adidas", "Lacoste", "Boss", "Oakley", "Tommy Hilfiger",
    "Calvin Klein", "Ralph Lauren", "The North Face", "New Era",
    "Champion", "Vans", "Puma", "Fila", "Levi's",
]

TAMANHOS_ROUPA = ["P", "M", "G", "GG", "XG"]
TAMANHOS_CALCADO = ["38", "39", "40", "41", "42", "43", "44"]
TAMANHO_UNICO = ["U"]

LINHAS = [
    "Classic", "Tech Fleece", "Slim Fit", "Essential", "Sport", "Premium",
    "Street", "Urban", "Signature", "Performance", "Regular Fit", "Comfort",
    "Heritage", "Icon", "Retro", "Air", "Pro", "Basic", "Oversized",
    "Relaxed Fit",
]

# categoria -> (tipos de peça, faixa de preço em R$, tabela de tamanhos)
#
# As 5 categorias marcadas abaixo (Polos, Bermudas Elastano, Jeans, Conjuntos,
# Sandálias) foram adicionadas em 08/08, não fazem parte do conjunto original
# — o usuário já as havia criado pelo Django Admin durante o cadastro manual
# dos produtos reais importados (ver importar_produtos_reais.py), e
# aplicar_variacoes_padrao.py (que reaproveita este dict) as encontrou como
# "não reconhecidas" na sua primeira execução real (77 produtos, "Conjuntos"
# sozinha respondendo por 64 deles). Faixa de preço e tipos de peça abaixo são
# só placeholders para o gerador de fixture (`gerar_preco()`/seed fictício) —
# não afetam os produtos reais já cadastrados, que já têm seu próprio `preco`
# definido à mão; escolhidos por proximidade com a categoria "irmã" mais
# parecida já existente, não por dado real de mercado:
#   - Polos: mesma faixa de Camisetas (peça de cima mais casual, preço similar).
#   - Bermudas Elastano: mesma faixa de Bermudas (mesma peça, variação de
#     tecido — elastano não muda a faixa de preço esperada).
#   - Jeans: mesma faixa de Calças (Calças já inclui "Calça Jeans" como tipo
#     de peça — Jeans aqui é a categoria dedicada para o mesmo tipo de item).
#   - Conjuntos: faixa mais alta que qualquer peça avulsa (acima até de
#     Jaquetas/Moletons) — é peça composta (2+ itens, ex: "Kit Completo
#     Lacoste", "Conjunto Boss 2026"), preço de conjunto reflete a soma de
#     mais de uma peça, não uma peça só.
#   - Sandálias: mesma tabela de tamanhos de Tênis (TAMANHOS_CALCADO), mas
#     faixa de preço mais baixa — sandália/chinelo/slide historicamente vende
#     mais barato que tênis no mesmo público.
#
# Adicionado 10/08 — "Acessórios" deixou de ser o único guarda-chuva para
# óculos/cinto/carteira/relógio: essas quatro passaram a ser Categoria reais
# no banco (ver produtos/management/commands/criar_categorias_acessorios.py),
# para que cada uma apareça como sua própria coluna no dropdown "Acessórios"
# do Header (HeaderNav.jsx) em vez de ficarem escondidas como "tipo de peça"
# dentro de uma única categoria. Faixas de preço, de novo, são só chute
# razoável para o gerador de fixture — não pesquisa de mercado real:
#   - Relógios/Óculos: ticket historicamente mais alto que cinto/carteira no
#     mesmo segmento (streetwear/grife) — faixa mais alta que as outras três.
#   - Cintos/Carteiras: acessórios de couro/sintético mais simples, ticket
#     mais baixo — faixas próximas uma da outra.
# "Acessórios" continua existindo como categoria (não foi removida) — vira o
# catch-all para o que não se encaixa nas quatro novas (ex: shoulder bag);
# por isso seu tipo de peça mudou de "Mochila" para "Shoulder Bag" e perdeu
# "Óculos"/"Cinto"/"Carteira" da lista (esses três tipos agora têm categoria
# própria, listá-los aqui também seria redundante/confuso para o gerador de
# fixture). Produtos reais que já existem sob "Acessórios" hoje NÃO são
# recategorizados automaticamente por essa mudança — ver CLAUDE.md.
CATEGORIAS_CONFIG = {
    "Camisetas": (["Camiseta"], (120, 450), TAMANHOS_ROUPA),
    "Polos": (["Polo"], (120, 450), TAMANHOS_ROUPA),
    "Bermudas": (["Bermuda"], (150, 500), TAMANHOS_ROUPA),
    "Bermudas Elastano": (["Bermuda"], (150, 500), TAMANHOS_ROUPA),
    "Calças": (["Calça", "Calça Jeans"], (220, 700), TAMANHOS_ROUPA),
    "Jeans": (["Calça Jeans"], (220, 700), TAMANHOS_ROUPA),
    "Jaquetas/Moletons": (["Jaqueta", "Moletom", "Corta-Vento"], (350, 1200), TAMANHOS_ROUPA),
    "Conjuntos": (["Conjunto", "Kit"], (400, 1500), TAMANHOS_ROUPA),
    "Bonés": (["Boné"], (120, 350), TAMANHO_UNICO),
    "Tênis": (["Tênis"], (400, 2000), TAMANHOS_CALCADO),
    "Sandálias": (["Sandália", "Slide", "Chinelo"], (150, 700), TAMANHOS_CALCADO),
    "Acessórios": (["Shoulder Bag"], (80, 600), TAMANHO_UNICO),
    "Relógios": (["Relógio"], (300, 2500), TAMANHO_UNICO),
    "Óculos": (["Óculos"], (150, 900), TAMANHO_UNICO),
    "Cintos": (["Cinto"], (80, 350), TAMANHO_UNICO),
    "Carteiras": (["Carteira"], (100, 450), TAMANHO_UNICO),
}

TOTAL_PRODUTOS = 50

# Semente fixa: torna a geração determinística entre execuções, então rodar
# o comando de novo gera os MESMOS ~50 nomes de produto (não um lote novo de
# 50 aleatórios) — é isso que faz o get_or_create abaixo realmente pular
# tudo já existente numa segunda execução, em vez de só evitar o erro de
# unique_together sem evitar duplicar produtos com nomes diferentes a cada
# rodada.
SEED = 42


def gerar_preco(faixa, rng):
    minimo, maximo = faixa
    base = rng.randrange(minimo, maximo, 10)
    # Preço "quebrado" (ex: R$199,90) é o padrão do varejo brasileiro —
    # mais plausível que um valor redondo.
    return Decimal(base) - Decimal("0.10")


def gerar_estoque(rng):
    # Distribuição propositalmente desbalanceada: uma fatia pequena em 0
    # (testa o estado "Esgotado"), outra fatia pequena baixa (1-3), e a
    # maioria em estoque normal — mesma mistura pedida para exercitar o
    # catálogo/variações visualmente.
    roll = rng.random()
    if roll < 0.15:
        return 0
    if roll < 0.30:
        return rng.randint(1, 3)
    return rng.randint(5, 30)


class Command(BaseCommand):
    help = (
        "Popula o banco de desenvolvimento com categorias, marcas, produtos "
        "e variações fictícias (mas plausíveis) para testar o catálogo, "
        "filtros e o novo tema visual. Idempotente: rodar de novo não "
        "duplica produtos/variações já criados por uma execução anterior."
    )

    def handle(self, *args, **options):
        rng = random.Random(SEED)

        categorias = self._seed_categorias()
        marcas = self._seed_marcas()

        produtos_criados = 0
        produtos_existentes = 0
        variacoes_criadas = 0
        variacoes_existentes = 0

        nomes_categorias = list(CATEGORIAS_CONFIG.keys())
        # Distribui os ~50 produtos de forma equilibrada entre as
        # categorias (algumas ficam com 1 produto a mais que outras quando
        # TOTAL_PRODUTOS não é múltiplo exato da quantidade de categorias).
        base, resto = divmod(TOTAL_PRODUTOS, len(nomes_categorias))
        quantidades_por_categoria = [
            base + (1 if i < resto else 0) for i in range(len(nomes_categorias))
        ]

        for nome_categoria, quantidade in zip(nomes_categorias, quantidades_por_categoria):
            tipos, faixa_preco, tabela_tamanhos = CATEGORIAS_CONFIG[nome_categoria]
            categoria = categorias[nome_categoria]

            # Combinações (tipo, marca, linha) embaralhadas de forma
            # determinística (mesma seed) e consumidas em ordem — garante
            # nomes de produto únicos dentro da própria execução, sem
            # depender de sorteio-com-retry.
            combinacoes = [
                (tipo, marca_nome, linha)
                for tipo in tipos
                for marca_nome in MARCAS
                for linha in LINHAS
            ]
            rng.shuffle(combinacoes)

            for tipo, marca_nome, linha in combinacoes[:quantidade]:
                nome_produto = f"{tipo} {marca_nome} {linha}"
                preco = gerar_preco(faixa_preco, rng)

                produto, criado = Produto.objects.get_or_create(
                    nome=nome_produto,
                    defaults={
                        "preco": preco,
                        "marca": marcas[marca_nome],
                        "categoria": categoria,
                    },
                )
                if criado:
                    produtos_criados += 1
                else:
                    produtos_existentes += 1

                if len(tabela_tamanhos) == 1:
                    tamanhos_produto = tabela_tamanhos
                else:
                    quantidade_tamanhos = rng.randint(3, 5)
                    tamanhos_produto = rng.sample(
                        tabela_tamanhos, min(quantidade_tamanhos, len(tabela_tamanhos))
                    )

                for tamanho in tamanhos_produto:
                    _, criada = Variacao.objects.get_or_create(
                        produto=produto,
                        tamanho=tamanho,
                        defaults={"estoque": gerar_estoque(rng)},
                    )
                    if criada:
                        variacoes_criadas += 1
                    else:
                        variacoes_existentes += 1

        self.stdout.write(self.style.SUCCESS("Seed de produtos concluído."))
        self.stdout.write(f"Categorias no banco: {len(categorias)}")
        self.stdout.write(f"Marcas no banco: {len(marcas)}")
        self.stdout.write(
            f"Produtos criados: {produtos_criados} "
            f"(já existiam e foram pulados: {produtos_existentes})"
        )
        self.stdout.write(
            f"Variações criadas: {variacoes_criadas} "
            f"(já existiam e foram puladas: {variacoes_existentes})"
        )

    def _seed_categorias(self):
        categorias = {}
        criadas = 0
        for nome in CATEGORIAS_CONFIG:
            categoria, criada = Categoria.objects.get_or_create(nome=nome)
            categorias[nome] = categoria
            if criada:
                criadas += 1
        self.stdout.write(f"Categorias novas criadas nesta execução: {criadas}")
        return categorias

    def _seed_marcas(self):
        marcas = {}
        criadas = 0
        for nome in MARCAS:
            marca, criada = Marca.objects.get_or_create(nome=nome)
            marcas[nome] = marca
            if criada:
                criadas += 1
        self.stdout.write(f"Marcas novas criadas nesta execução: {criadas}")
        return marcas

from django.core.management.base import BaseCommand

from produtos.models import Categoria

# "Óculos"/"Cinto"/"Carteira" existiam até aqui só como "tipo de peça" dentro
# da Categoria "Acessórios" (ver CATEGORIAS_CONFIG, seed_produtos.py) — não
# como Categoria real, então não podiam virar sua própria coluna no dropdown
# "Acessórios" do Header (HeaderNav.jsx). "Relógios" é inteiramente novo,
# nem existia como tipo de peça antes. Ver CLAUDE.md para o contexto
# completo dessa reorganização.
#
# "Shoulder Bag"/"Meias" adicionadas na rodada seguinte, mesmo dia (10/08):
# mesma lógica — "Shoulder Bag" era o único `tipo` dentro do catch-all
# "Outros Acessórios" (ver CATEGORIAS_CONFIG), "Meias" é inteiramente nova.
# Ao mesmo tempo, "Outros Acessórios" (o catch-all em si) foi REMOVIDA de
# NOMES_CATEGORIAS_ACESSORIO (HeaderNav.jsx) — ela continua existindo como
# Categoria, só não aparece mais como coluna neste dropdown; produtos nela
# ficam "órfãos" de navegação até recategorizados manualmente — ver
# CLAUDE.md para a lista completa.
NOMES_CATEGORIAS = ["Relógios", "Óculos", "Cintos", "Carteiras", "Shoulder Bag", "Meias"]


class Command(BaseCommand):
    help = (
        "Cria as Categoria 'Relógios', 'Óculos', 'Cintos', 'Carteiras', "
        "'Shoulder Bag' e 'Meias' (get_or_create, mesmo padrão de "
        "seed_produtos.py), separando-as do guarda-chuva único 'Outros "
        "Acessórios' para que cada uma apareça como sua própria coluna no "
        "dropdown 'Acessórios' do Header. Só cria as Categoria em si — NÃO "
        "recategoriza nenhum Produto existente; produtos hoje cadastrados "
        "sob 'Outros Acessórios' continuam lá até serem recategorizados "
        "manualmente pelo usuário no Django Admin. Idempotente via "
        "get_or_create: rodar de novo não duplica nada."
    )

    def handle(self, *args, **options):
        criadas = 0
        existentes = 0

        for nome in NOMES_CATEGORIAS:
            _, criada = Categoria.objects.get_or_create(nome=nome)
            if criada:
                criadas += 1
            else:
                existentes += 1
            self.stdout.write(f"  - {nome!r}: {'criada' if criada else 'já existia'}")

        self.stdout.write(self.style.SUCCESS("Categorias de acessórios prontas."))
        self.stdout.write(f"Criadas nesta execução: {criadas}")
        self.stdout.write(f"Já existiam: {existentes}")

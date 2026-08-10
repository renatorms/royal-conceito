from django.core.management.base import BaseCommand

from produtos.models import Categoria

NOME_CATEGORIA = "Cuecas"


class Command(BaseCommand):
    help = (
        "Cria a Categoria 'Cuecas' (get_or_create, mesmo padrão idempotente "
        "de criar_categorias_acessorios.py) — categoria de roupa (não "
        "acessório), aparece no dropdown 'Roupas' do Header, não "
        "'Acessórios', via TAMANHOS_ROUPA em CATEGORIAS_CONFIG "
        "(seed_produtos.py). Confirmado via shell antes de escrever este "
        "comando que 'Cuecas' ainda não existia no banco "
        "(Categoria.objects.filter(nome__icontains='cueca') vazio) — "
        "diferente de outras categorias novas deste projeto (Conjuntos, "
        "Jeans, Polos, etc), que já tinham sido criadas à mão pelo usuário "
        "antes do backend ser atualizado para reconhecê-las."
    )

    def handle(self, *args, **options):
        _, criada = Categoria.objects.get_or_create(nome=NOME_CATEGORIA)
        if criada:
            self.stdout.write(self.style.SUCCESS(f"Categoria {NOME_CATEGORIA!r} criada."))
        else:
            self.stdout.write(f"Categoria {NOME_CATEGORIA!r} já existia — nada a fazer.")

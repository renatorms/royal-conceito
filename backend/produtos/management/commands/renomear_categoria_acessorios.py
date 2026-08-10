from django.core.management.base import BaseCommand

from produtos.models import Categoria

NOME_ANTIGO = "Acessórios"
NOME_NOVO = "Outros Acessórios"


class Command(BaseCommand):
    help = (
        "Renomeia a Categoria catch-all 'Acessórios' para 'Outros Acessórios' "
        "(mesma linha no banco, só o campo `nome` muda — nenhum Produto é "
        "recategorizado ou perde vínculo). Feito via management command, não "
        "uma migration de dados, mesmo padrão idempotente já usado pelos "
        "outros comandos deste app (seed_produtos.py, "
        "criar_categorias_acessorios.py, etc). Motivo: o dropdown "
        "'Acessórios' do Header (label do NavDropdown, não muda) passou a "
        "mostrar uma coluna também chamada 'Acessórios' (a própria "
        "categoria catch-all) ao lado de Relógios/Óculos/Cintos/Carteiras, "
        "lendo como repetição confusa. Idempotente: se 'Acessórios' já não "
        "existir mais (renomeada numa execução anterior), não faz nada."
    )

    def handle(self, *args, **options):
        categoria = Categoria.objects.filter(nome=NOME_ANTIGO).first()

        if categoria is not None:
            categoria.nome = NOME_NOVO
            categoria.save(update_fields=["nome"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Categoria [{categoria.id}] renomeada de {NOME_ANTIGO!r} para {NOME_NOVO!r}."
                )
            )
            return

        if Categoria.objects.filter(nome=NOME_NOVO).exists():
            self.stdout.write(f"Já renomeada — {NOME_NOVO!r} já existe, nada a fazer.")
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Nenhuma Categoria chamada {NOME_ANTIGO!r} ou {NOME_NOVO!r} encontrada."
                )
            )

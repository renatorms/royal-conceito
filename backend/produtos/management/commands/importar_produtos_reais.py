import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from produtos.models import Produto

# frontend/public/produtos/ — fotos reais de produtos já salvas manualmente
# pelo usuário (fora do controle deste backend, não geradas por nenhum
# comando). settings.BASE_DIR aqui é backend/ (ver core/settings.py), então
# o diretório do frontend é o irmão de backend/ na raiz do repositório.
DIRETORIO_IMAGENS = settings.BASE_DIR.parent / "frontend" / "public" / "produtos"

EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp"}

# Caracteres tratados como separador de palavra ao derivar o nome do produto
# a partir do nome do arquivo — hífen e "=" (visto em pelo menos um arquivo
# real, "CONJUNTO-LACOSTE=DRI-FIT.jpg"). Apóstrofo é deliberadamente mantido
# fora dessa lista (não é separador): "OVERSIZED'S..." vira "Oversized's...",
# não "Oversized S...".
SEPARADORES = re.compile(r"[-_=]+")


def nome_produto_a_partir_do_arquivo(caminho):
    """Deriva um nome de produto legível a partir do nome do arquivo.

    Ex: "CONJUNTO-LACOSTE-2026.jpg" -> "Conjunto Lacoste 2026".
    str.capitalize() (não .title()) por palavra: só a primeira letra da
    palavra vira maiúscula, o resto sempre minúsculo — evita o artefato do
    .title() em "OVERSIZED'S" (que capitalizaria o S depois do apóstrofo).
    Não há como recuperar acentos que o nome do arquivo já não tinha (ex:
    "TENIS" -> "Tenis", não "Tênis") — correção fica para o cadastro manual.
    """
    base = caminho.stem  # remove a extensão
    com_espacos = SEPARADORES.sub(" ", base)
    palavras = com_espacos.split()  # também colapsa espaços múltiplos/já existentes no nome
    return " ".join(palavra.capitalize() for palavra in palavras)


class Command(BaseCommand):
    help = (
        "Cria um Produto real para cada imagem em frontend/public/produtos/, "
        "derivando o nome a partir do nome do arquivo. Cada Produto é criado "
        "com preco=0 (placeholder óbvio, precisa ser corrigido à mão), "
        "categoria=None e marca=None (idem), e imagem_url apontando para o "
        "caminho público servido pelo Vite (\"/produtos/<arquivo>\"). Nenhuma "
        "Variacao é criada — tamanho/estoque reais dependem de informação "
        "que só o usuário tem, preenchimento fica para o Django Admin. "
        "Idempotente: identifica produtos já importados pelo próprio "
        "imagem_url, então rodar de novo não duplica nada."
    )

    def handle(self, *args, **options):
        if not DIRETORIO_IMAGENS.is_dir():
            raise CommandError(f"Diretório não encontrado: {DIRETORIO_IMAGENS}")

        arquivos = sorted(
            caminho
            for caminho in DIRETORIO_IMAGENS.iterdir()
            if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_VALIDAS
        )
        if not arquivos:
            raise CommandError(f"Nenhuma imagem encontrada em {DIRETORIO_IMAGENS}")

        criados = 0
        existentes = 0
        for arquivo in arquivos:
            imagem_url = f"/produtos/{arquivo.name}"
            _, criado = Produto.objects.get_or_create(
                imagem_url=imagem_url,
                defaults={
                    "nome": nome_produto_a_partir_do_arquivo(arquivo),
                    "preco": 0,
                    "marca": None,
                    "categoria": None,
                },
            )
            if criado:
                criados += 1
            else:
                existentes += 1

        self.stdout.write(self.style.SUCCESS("Importação de produtos reais concluída."))
        self.stdout.write(f"Imagens encontradas: {len(arquivos)}")
        self.stdout.write(
            f"Produtos criados: {criados} (já existiam e foram pulados: {existentes})"
        )

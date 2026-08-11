from django.core.management.base import BaseCommand

from produtos.models import Categoria, Produto, Variacao

# Parte 1 — os 5 produtos "órfãos" (ver CLAUDE.md) cujo nome já deixava
# claro para qual das novas categorias específicas cada um deveria ir,
# listados quando "Outros Acessórios" foi removida do dropdown do Header.
# Recategorização direta, sem ambiguidade — não envolve o produto Oakley
# combinado (id 181, tratado à parte na Parte 2 abaixo).
RECATEGORIZACOES = {
    91: "Bonés",
    94: "Carteiras",
    95: "Cintos",
    168: "Cuecas",
    187: "Relógios",
}

# Parte 2 — produto [181] "Oculos e Relogios Oakley 1linha" era, na
# verdade, dois itens diferentes (óculos + relógio) cadastrados como um
# produto só. Investigado antes de separar: tinha exatamente 1 Variacao
# (tamanho="U", estoque=10) — um estoque único cobrindo o lote combinado,
# não um número por item. Separado em dois produtos reais, cada um com
# estoque=10 (não metade, não zero — decisão do usuário: ambos ficam com o
# mesmo valor por ora, para checagem visual, sabendo que não reflete a
# contagem real por item; ajuste fica para o usuário depois que o estoque
# real de cada um for conferido).
ID_PRODUTO_OAKLEY_ORIGINAL = 181
NOME_OCULOS_OAKLEY = "Oculos Oakley 1a Linha"
CATEGORIA_OCULOS_OAKLEY = "Óculos"
NOME_RELOGIO_OAKLEY = "Relogio Oakley 1a Linha"
CATEGORIA_RELOGIO_OAKLEY = "Relógios"
TAMANHO_VARIACAO_SPLIT = "U"
ESTOQUE_VARIACAO_SPLIT = 10


class Command(BaseCommand):
    help = (
        "Resolve os produtos que ficaram 'órfãos' de navegação no Header "
        "depois que 'Outros Acessórios' saiu do dropdown 'Acessórios' (ver "
        "CLAUDE.md). Parte 1: recategoriza diretamente os 5 produtos cujo "
        "nome já indicava a categoria certa. Parte 2: separa o produto "
        "combinado 'Oculos e Relogios Oakley 1linha' (id 181) em dois "
        "produtos reais — o original vira só 'Oculos Oakley 1a Linha' "
        "(mesmo id, mesma Variacao existente), e um novo 'Relogio Oakley 1a "
        "Linha' é criado do zero, reaproveitando marca/imagem_url/preço do "
        "original (preço e imagem são pendência de ajuste manual — ver "
        "CLAUDE.md) e com sua própria Variacao (tamanho='U', estoque=10). "
        "Idempotente: rodar de novo não recategoriza o que já está certo "
        "nem duplica o produto/variação do split."
    )

    def handle(self, *args, **options):
        self._recategorizar_produtos_orfaos()
        self._separar_produto_oakley()

    def _recategorizar_produtos_orfaos(self):
        self.stdout.write("--- Parte 1: recategorização direta ---")
        for produto_id, nome_categoria_nova in RECATEGORIZACOES.items():
            try:
                produto = Produto.objects.select_related("categoria").get(id=produto_id)
            except Produto.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Produto id {produto_id} não encontrado — pulado.")
                )
                continue

            categoria_nova = Categoria.objects.get(nome=nome_categoria_nova)
            categoria_atual_nome = produto.categoria.nome if produto.categoria else None

            if produto.categoria_id == categoria_nova.id:
                self.stdout.write(
                    f"[{produto.id}] {produto.nome!r}: já está em {nome_categoria_nova!r} — nada a fazer."
                )
                continue

            self.stdout.write(
                f"[{produto.id}] {produto.nome!r}: {categoria_atual_nome!r} -> {nome_categoria_nova!r}"
            )
            produto.categoria = categoria_nova
            produto.save(update_fields=["categoria"])
            self.stdout.write(f"  confirmado: categoria agora é {produto.categoria.nome!r}")

    def _separar_produto_oakley(self):
        self.stdout.write("--- Parte 2: separação do produto Oakley combinado ---")
        try:
            original = Produto.objects.select_related("marca", "categoria").prefetch_related(
                "variacoes"
            ).get(id=ID_PRODUTO_OAKLEY_ORIGINAL)
        except Produto.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"Produto id {ID_PRODUTO_OAKLEY_ORIGINAL} não encontrado — split pulado."
                )
            )
            return

        categoria_oculos = Categoria.objects.get(nome=CATEGORIA_OCULOS_OAKLEY)

        if original.nome == NOME_OCULOS_OAKLEY and original.categoria_id == categoria_oculos.id:
            self.stdout.write(
                f"[{original.id}] já é {NOME_OCULOS_OAKLEY!r} em {CATEGORIA_OCULOS_OAKLEY!r} — nada a fazer."
            )
        else:
            categoria_atual_nome = original.categoria.nome if original.categoria else None
            self.stdout.write(
                f"[{original.id}] {original.nome!r} ({categoria_atual_nome!r}) "
                f"-> {NOME_OCULOS_OAKLEY!r} ({CATEGORIA_OCULOS_OAKLEY!r})"
            )
            original.nome = NOME_OCULOS_OAKLEY
            original.categoria = categoria_oculos
            original.save(update_fields=["nome", "categoria"])

        variacao_original = original.variacoes.first()
        self.stdout.write(
            f"  Variacao existente mantida como está: "
            f"tamanho={variacao_original.tamanho!r}, estoque={variacao_original.estoque} "
            f"(confirmado, não alterada)"
            if variacao_original
            else "  (produto original não tem nenhuma Variacao — nada a confirmar)"
        )

        categoria_relogio = Categoria.objects.get(nome=CATEGORIA_RELOGIO_OAKLEY)
        relogio, relogio_criado = Produto.objects.get_or_create(
            nome=NOME_RELOGIO_OAKLEY,
            defaults={
                "preco": original.preco,
                "categoria": categoria_relogio,
                "marca": original.marca,
                "imagem_url": original.imagem_url,
            },
        )
        if relogio_criado:
            marca_nome = relogio.marca.nome if relogio.marca else None
            self.stdout.write(
                f"[{relogio.id}] {NOME_RELOGIO_OAKLEY!r} criado — categoria "
                f"{CATEGORIA_RELOGIO_OAKLEY!r}, marca {marca_nome!r}, "
                f"preco {relogio.preco} (mesmo do original — pendência de ajuste manual), "
                f"imagem_url {relogio.imagem_url!r} (reaproveitada do original — pendência de "
                f"foto real separada)"
            )
        else:
            self.stdout.write(
                f"[{relogio.id}] {NOME_RELOGIO_OAKLEY!r} já existia — nada a fazer."
            )

        _, variacao_criada = Variacao.objects.get_or_create(
            produto=relogio,
            tamanho=TAMANHO_VARIACAO_SPLIT,
            defaults={"estoque": ESTOQUE_VARIACAO_SPLIT},
        )
        if variacao_criada:
            self.stdout.write(
                f"  Variacao criada: tamanho={TAMANHO_VARIACAO_SPLIT!r}, estoque={ESTOQUE_VARIACAO_SPLIT}"
            )
        else:
            self.stdout.write("  Variacao já existia — nada a fazer.")

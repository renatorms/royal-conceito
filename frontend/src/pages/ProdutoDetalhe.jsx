import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { buscarProduto } from "@/api/produtos";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { cn, formatarPreco } from "@/lib/utils";

export default function ProdutoDetalhe() {
  const { id } = useParams();
  const [resultado, setResultado] = useState({ id: null, produto: null, erro: null });
  const isLoading = resultado.id !== id;

  useEffect(() => {
    let ignore = false;

    buscarProduto(id)
      .then((data) => {
        if (!ignore) setResultado({ id, produto: data, erro: null });
      })
      .catch(() => {
        if (!ignore) setResultado({ id, produto: null, erro: "Produto não encontrado." });
      });

    return () => {
      ignore = true;
    };
  }, [id]);

  if (isLoading) {
    return (
      <p className="mx-auto max-w-3xl px-4 py-16 text-sm text-muted-foreground">
        Carregando produto...
      </p>
    );
  }

  if (resultado.erro || !resultado.produto) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="text-sm text-destructive">{resultado.erro ?? "Produto não encontrado."}</p>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Voltar ao catálogo
        </Link>
      </div>
    );
  }

  const produto = resultado.produto;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
        ← Voltar ao catálogo
      </Link>

      <div className="mt-4 grid gap-6 sm:grid-cols-2">
        <ProdutoImagemPlaceholder className="rounded-xl" />

        <div className="flex flex-col gap-3">
          {produto.marca_nome && (
            <span className="text-sm text-muted-foreground">{produto.marca_nome}</span>
          )}
          <h1 className="text-2xl font-semibold">{produto.nome}</h1>
          {produto.categoria_nome && (
            <span className="text-sm text-muted-foreground">{produto.categoria_nome}</span>
          )}
          <span className="text-xl font-semibold">{formatarPreco(produto.preco)}</span>

          <div className="mt-2">
            <h2 className="mb-2 text-sm font-medium">Tamanhos disponíveis</h2>
            {produto.variacoes.length === 0 ? (
              <p className="text-sm text-muted-foreground">Sem variações cadastradas.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {produto.variacoes.map((variacao) => {
                  const semEstoque = variacao.estoque <= 0;
                  return (
                    <span
                      key={variacao.id}
                      aria-disabled={semEstoque}
                      className={cn(
                        "flex min-w-12 flex-col items-center justify-center gap-0.5 rounded-md border border-border px-3 py-1.5 text-sm",
                        semEstoque && "cursor-not-allowed border-dashed opacity-50"
                      )}
                    >
                      <span className={cn(semEstoque && "text-muted-foreground line-through")}>
                        {variacao.tamanho}
                      </span>
                      {semEstoque && (
                        <span className="text-[10px] leading-none text-muted-foreground">
                          Esgotado
                        </span>
                      )}
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

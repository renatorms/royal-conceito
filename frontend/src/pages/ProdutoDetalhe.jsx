import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { MinusIcon, PlusIcon } from "lucide-react";
import { buscarProduto } from "@/api/produtos";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { Button } from "@/components/ui/button";
import { useCart } from "@/contexts/CartContext";
import { cn, formatarPreco } from "@/lib/utils";

const FEEDBACK_DURATION_MS = 1500;

export default function ProdutoDetalhe() {
  const { id } = useParams();
  const { adicionarItem } = useCart();
  const [resultado, setResultado] = useState({ id: null, produto: null, erro: null });
  const [variacaoId, setVariacaoId] = useState(null);
  const [quantidade, setQuantidade] = useState(1);
  const [adicionado, setAdicionado] = useState(false);
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

  useEffect(() => {
    setVariacaoId(null);
    setQuantidade(1);
    setAdicionado(false);
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
  const variacaoSelecionada = produto.variacoes.find((v) => v.id === variacaoId) || null;

  function selecionarVariacao(variacao) {
    if (variacao.estoque <= 0) return;
    setVariacaoId(variacao.id);
    setQuantidade(1);
    setAdicionado(false);
  }

  function alterarQuantidade(delta) {
    if (!variacaoSelecionada) return;
    setQuantidade((atual) => Math.min(Math.max(atual + delta, 1), variacaoSelecionada.estoque));
  }

  function handleAdicionar() {
    if (!variacaoSelecionada) return;
    adicionarItem(produto, variacaoSelecionada, quantidade);
    setAdicionado(true);
    setTimeout(() => setAdicionado(false), FEEDBACK_DURATION_MS);
  }

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
                  const selecionada = variacao.id === variacaoId;
                  return (
                    <button
                      key={variacao.id}
                      type="button"
                      disabled={semEstoque}
                      aria-pressed={selecionada}
                      onClick={() => selecionarVariacao(variacao)}
                      className={cn(
                        "flex min-w-12 flex-col items-center justify-center gap-0.5 rounded-md border border-border px-3 py-1.5 text-sm transition-colors",
                        semEstoque && "cursor-not-allowed border-dashed opacity-50",
                        !semEstoque && "hover:border-primary",
                        selecionada && "border-primary bg-primary/10"
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
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {variacaoSelecionada && (
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">Quantidade</span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon-sm"
                  aria-label="Diminuir quantidade"
                  disabled={quantidade <= 1}
                  onClick={() => alterarQuantidade(-1)}
                >
                  <MinusIcon />
                </Button>
                <span className="w-6 text-center text-sm">{quantidade}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="icon-sm"
                  aria-label="Aumentar quantidade"
                  disabled={quantidade >= variacaoSelecionada.estoque}
                  onClick={() => alterarQuantidade(1)}
                >
                  <PlusIcon />
                </Button>
              </div>
            </div>
          )}

          <Button type="button" disabled={!variacaoSelecionada} onClick={handleAdicionar}>
            {adicionado ? "Adicionado!" : "Adicionar ao carrinho"}
          </Button>
        </div>
      </div>
    </div>
  );
}

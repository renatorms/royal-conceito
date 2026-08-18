import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { HeartIcon, MinusIcon, PlusIcon } from "lucide-react";
import { buscarProduto, listarProdutos } from "@/api/produtos";
import { criarFavorito, deletarFavorito, listarFavoritos } from "@/api/favoritos";
import { ProdutoCard } from "@/components/ProdutoCard";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/contexts/CartContext";
import { cn, formatarPreco } from "@/lib/utils";

const FEEDBACK_DURATION_MS = 1500;

// Número de parcelas exibido em "ou 10x de R$ XX,XX sem juros". Ajustável
// aqui caso o parcelamento real do gateway de pagamento seja diferente.
const NUMERO_PARCELAS = 10;

const MAX_MAIS_PRODUTOS = 8;

export default function ProdutoDetalhe() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { adicionarItem } = useCart();
  const { isAuthenticated } = useAuth();
  const [resultado, setResultado] = useState({ id: null, produto: null, erro: null });
  const [variacaoId, setVariacaoId] = useState(null);
  const [quantidade, setQuantidade] = useState(1);
  const [adicionado, setAdicionado] = useState(false);
  const [resultadoMaisProdutos, setResultadoMaisProdutos] = useState({ id: null, produtos: [] });
  const [resultadoFavorito, setResultadoFavorito] = useState({ id: null, favoritoId: null });
  const isLoading = resultado.id !== id;
  const maisProdutos = resultadoMaisProdutos.id === id ? resultadoMaisProdutos.produtos : [];
  const favoritoId = resultadoFavorito.id === id ? resultadoFavorito.favoritoId : null;
  const isFavorito = favoritoId !== null;

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

  useEffect(() => {
    let ignore = false;

    if (!resultado.produto?.categoria) return undefined;

    listarProdutos({ categoria: resultado.produto.categoria })
      .then((data) => {
        if (ignore) return;
        const relacionados = data.results
          .filter((p) => p.id !== resultado.produto.id)
          .slice(0, MAX_MAIS_PRODUTOS);
        setResultadoMaisProdutos({ id, produtos: relacionados });
      })
      .catch(() => {
        if (!ignore) setResultadoMaisProdutos({ id, produtos: [] });
      });

    return () => {
      ignore = true;
    };
  }, [id, resultado.produto]);

  useEffect(() => {
    let ignore = false;

    if (!isAuthenticated || !resultado.produto) return undefined;

    listarFavoritos()
      .then((favoritos) => {
        if (ignore) return;
        const favorito = favoritos.find((f) => f.produto.id === resultado.produto.id);
        setResultadoFavorito({ id, favoritoId: favorito ? favorito.id : null });
      })
      .catch(() => {
        if (!ignore) setResultadoFavorito({ id, favoritoId: null });
      });

    return () => {
      ignore = true;
    };
  }, [id, isAuthenticated, resultado.produto]);

  async function handleToggleFavorito() {
    if (!isAuthenticated) {
      navigate("/login", { state: { from: location } });
      return;
    }

    if (isFavorito) {
      const favoritoIdAtual = favoritoId;
      setResultadoFavorito({ id, favoritoId: null });
      try {
        await deletarFavorito(favoritoIdAtual);
      } catch {
        setResultadoFavorito({ id, favoritoId: favoritoIdAtual });
      }
      return;
    }

    setResultadoFavorito({ id, favoritoId: "pendente" });
    try {
      const favorito = await criarFavorito(resultado.produto.id);
      setResultadoFavorito({ id, favoritoId: favorito.id });
    } catch {
      setResultadoFavorito({ id, favoritoId: null });
    }
  }

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
  const imagemSrc = produto.imagem || produto.imagem_url;

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
        {imagemSrc ? (
          <img
            src={imagemSrc}
            alt={produto.nome}
            className="aspect-square w-full rounded-xl object-cover"
          />
        ) : (
          <ProdutoImagemPlaceholder className="rounded-xl" />
        )}

        <div className="flex flex-col gap-3">
          {produto.marca_nome && (
            <span className="text-sm text-muted-foreground">{produto.marca_nome}</span>
          )}
          <div className="flex items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold">{produto.nome}</h1>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={isFavorito ? "Remover dos favoritos" : "Adicionar aos favoritos"}
              aria-pressed={isFavorito}
              onClick={handleToggleFavorito}
            >
              <HeartIcon className={cn(isFavorito && "fill-destructive text-destructive")} />
            </Button>
          </div>
          {produto.categoria_nome && (
            <span className="text-sm text-muted-foreground">{produto.categoria_nome}</span>
          )}
          <span className="text-xl font-semibold">{formatarPreco(produto.preco)}</span>
          <span className="text-sm text-muted-foreground">
            ou {NUMERO_PARCELAS}x de {formatarPreco(produto.preco / NUMERO_PARCELAS)} sem juros
          </span>

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

      {produto.detalhes && (
        <div className="mt-10">
          <h2 className="mb-2 text-lg font-semibold">Detalhes do produto</h2>
          <p className="whitespace-pre-line text-sm text-muted-foreground">{produto.detalhes}</p>
        </div>
      )}

      {maisProdutos.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 text-lg font-semibold">Mais produtos</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {maisProdutos.map((produtoRelacionado) => (
              <ProdutoCard key={produtoRelacionado.id} produto={produtoRelacionado} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

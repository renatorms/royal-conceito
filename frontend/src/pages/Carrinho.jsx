import { Link, useLocation } from "react-router-dom";
import { MinusIcon, PlusIcon, XIcon } from "lucide-react";
import { useCart } from "@/contexts/CartContext";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { Button } from "@/components/ui/button";
import { formatarPreco } from "@/lib/utils";

export default function Carrinho() {
  const { itens, removerItem, atualizarQuantidade, totalValor } = useCart();
  const location = useLocation();

  if (itens.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          {location.state?.mensagem ?? "Seu carrinho está vazio."}
        </p>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Ver catálogo
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Carrinho</h1>

      <div className="flex flex-col gap-4">
        {itens.map((item) => (
          <div
            key={item.itemId}
            className="flex flex-wrap items-center gap-4 rounded-xl border border-border p-3"
          >
            <ProdutoImagemPlaceholder className="size-20 shrink-0 rounded-md" />

            <div className="flex min-w-40 flex-1 flex-col gap-1">
              <Link
                to={`/produtos/${item.produtoId}`}
                className="text-sm font-medium hover:underline"
              >
                {item.produtoNome}
              </Link>
              <span className="text-xs text-muted-foreground">Tamanho: {item.tamanho}</span>
              <span className="text-sm text-muted-foreground">
                {formatarPreco(item.preco)} / un.
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                aria-label="Diminuir quantidade"
                onClick={() => atualizarQuantidade(item.itemId, item.quantidade - 1)}
              >
                <MinusIcon />
              </Button>
              <span className="w-6 text-center text-sm">{item.quantidade}</span>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                aria-label="Aumentar quantidade"
                disabled={item.quantidade >= item.estoque}
                onClick={() => atualizarQuantidade(item.itemId, item.quantidade + 1)}
              >
                <PlusIcon />
              </Button>
            </div>

            <span className="w-24 text-right text-sm font-semibold">
              {formatarPreco(item.preco * item.quantidade)}
            </span>

            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Remover item"
              onClick={() => removerItem(item.itemId)}
            >
              <XIcon />
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
        <span className="text-lg font-semibold">Total: {formatarPreco(totalValor)}</span>
        <Button size="lg" render={<Link to="/checkout" />}>
          Finalizar compra
        </Button>
      </div>
    </div>
  );
}

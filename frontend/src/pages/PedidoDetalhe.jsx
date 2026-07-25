import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { buscarPedido } from "@/api/pedidos";
import { PedidoStatusBadge } from "@/components/PedidoStatusBadge";
import { formatarPreco } from "@/lib/utils";

const RESULTADO_INICIAL = { chave: null, pedido: null, erro: null };

function formatarData(dataIso) {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeStyle: "short" }).format(
    new Date(dataIso)
  );
}

export default function PedidoDetalhe() {
  const { id } = useParams();
  const [resultado, setResultado] = useState(RESULTADO_INICIAL);
  const isLoading = resultado.chave !== id;

  useEffect(() => {
    let ignore = false;

    buscarPedido(id)
      .then((data) => {
        if (ignore) return;
        setResultado({ chave: id, pedido: data, erro: null });
      })
      .catch((error) => {
        if (ignore) return;
        setResultado({
          chave: id,
          pedido: null,
          erro:
            error.response?.status === 404
              ? "Pedido não encontrado."
              : "Não foi possível carregar este pedido.",
        });
      });

    return () => {
      ignore = true;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <p className="text-sm text-muted-foreground">Carregando pedido...</p>
      </div>
    );
  }

  if (resultado.erro) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="text-sm text-destructive">{resultado.erro}</p>
        <Link
          to="/meus-pedidos"
          className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Voltar para meus pedidos
        </Link>
      </div>
    );
  }

  const pedido = resultado.pedido;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link
        to="/meus-pedidos"
        className="mb-4 inline-block text-sm text-muted-foreground hover:text-foreground"
      >
        ← Voltar para meus pedidos
      </Link>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Pedido #{pedido.id}</h1>
          <p className="text-sm text-muted-foreground">{formatarData(pedido.data_pedido)}</p>
        </div>
        <PedidoStatusBadge status={pedido.status} />
      </div>

      <div className="flex flex-col gap-3">
        {pedido.itens.map((item) => (
          <div
            key={item.id}
            className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border p-4"
          >
            <div className="flex flex-col gap-1">
              <span className="text-sm font-medium">{item.produto_nome}</span>
              <span className="text-xs text-muted-foreground">
                Tamanho: {item.produto_tamanho} · Quantidade: {item.quantidade}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatarPreco(item.preco_unitario)} / un.
              </span>
            </div>
            <span className="text-sm font-semibold">{formatarPreco(item.subtotal)}</span>
          </div>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
        <span className="text-lg font-semibold">Total</span>
        <span className="text-lg font-semibold">{formatarPreco(pedido.total)}</span>
      </div>
    </div>
  );
}

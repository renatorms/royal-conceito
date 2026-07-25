import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listarPedidos } from "@/api/pedidos";
import { PedidoStatusBadge } from "@/components/PedidoStatusBadge";
import { Button } from "@/components/ui/button";
import { formatarPreco } from "@/lib/utils";

const PAGE_SIZE = 10;

const RESULTADO_INICIAL = {
  chave: null,
  pedidos: [],
  count: 0,
  next: null,
  previous: null,
  erro: null,
};

function formatarData(dataIso) {
  return new Intl.DateTimeFormat("pt-BR").format(new Date(dataIso));
}

export default function MeusPedidos() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page")) || 1;

  const [resultado, setResultado] = useState(RESULTADO_INICIAL);

  const chaveAtual = JSON.stringify({ page });
  const isLoading = resultado.chave !== chaveAtual;

  useEffect(() => {
    let ignore = false;

    listarPedidos({ page })
      .then((data) => {
        if (ignore) return;
        setResultado({
          chave: chaveAtual,
          pedidos: data.results,
          count: data.count,
          next: data.next,
          previous: data.previous,
          erro: null,
        });
      })
      .catch(() => {
        if (ignore) return;
        setResultado({
          chave: chaveAtual,
          pedidos: [],
          count: 0,
          next: null,
          previous: null,
          erro: "Não foi possível carregar seus pedidos.",
        });
      });

    return () => {
      ignore = true;
    };
  }, [page, chaveAtual]);

  function irParaPagina(novaPagina) {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      if (novaPagina > 1) {
        nextParams.set("page", String(novaPagina));
      } else {
        nextParams.delete("page");
      }
      return nextParams;
    });
  }

  const totalPaginas = Math.max(1, Math.ceil(resultado.count / PAGE_SIZE));

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Meus Pedidos</h1>

      {resultado.erro ? (
        <p className="text-sm text-destructive">{resultado.erro}</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando pedidos...</p>
      ) : resultado.pedidos.length === 0 ? (
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Você ainda não fez nenhum pedido.</p>
          <Link
            to="/"
            className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
          >
            Ver catálogo
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {resultado.pedidos.map((pedido) => (
            <Link
              key={pedido.id}
              to={`/meus-pedidos/${pedido.id}`}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border p-4 hover:border-primary/50"
            >
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium">Pedido #{pedido.id}</span>
                <span className="text-xs text-muted-foreground">
                  {formatarData(pedido.data_pedido)}
                </span>
              </div>
              <PedidoStatusBadge status={pedido.status} />
              <span className="text-sm font-semibold">{formatarPreco(pedido.total)}</span>
            </Link>
          ))}
        </div>
      )}

      {resultado.count > 0 && (
        <div className="mt-8 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={!resultado.previous}
            onClick={() => irParaPagina(page - 1)}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPaginas}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!resultado.next}
            onClick={() => irParaPagina(page + 1)}
          >
            Próxima
          </Button>
        </div>
      )}
    </div>
  );
}

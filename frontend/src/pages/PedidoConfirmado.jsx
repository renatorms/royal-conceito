import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { buscarPedido } from "@/api/pedidos";
import { PedidoStatusBadge } from "@/components/PedidoStatusBadge";
import { Button } from "@/components/ui/button";
import { formatarPreco } from "@/lib/utils";

const RESULTADO_INICIAL = { chave: null, pedido: null, erro: null };

// Destino do redirect_url mandado pra InfinitePay ao gerar o link de
// pagamento (ver PedidoViewSet.gerar_link_pagamento(), pedidos/views.py) —
// então o caminho normal até aqui é o cliente voltando de uma navegação de
// página inteira no site da InfinitePay, não um navigate() do React Router.
// Isso significa que não existe location.state vindo do Checkout.jsx nessa
// volta (é uma navegação nova, de fora do app) — o pedidoId chega só via
// query string. location.state ainda é checado como fallback, sem custo,
// caso essa página seja alcançada de outra forma no futuro.
export default function PedidoConfirmado() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const pedidoId = searchParams.get("pedidoId") || location.state?.pedidoId;

  const [resultado, setResultado] = useState(RESULTADO_INICIAL);
  const isLoading = pedidoId != null && resultado.chave !== pedidoId;

  useEffect(() => {
    if (pedidoId == null) return;

    let ignore = false;

    buscarPedido(pedidoId)
      .then((data) => {
        if (ignore) return;
        setResultado({ chave: pedidoId, pedido: data, erro: null });
      })
      .catch((error) => {
        if (ignore) return;
        setResultado({
          chave: pedidoId,
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
  }, [pedidoId]);

  function handleAtualizar() {
    // Confirmação de pagamento chega via webhook, de forma assíncrona (ver
    // CLAUDE.md) — pode não ter processado ainda no instante em que a
    // InfinitePay redireciona o cliente de volta pra cá. Em vez de tentar
    // adivinhar um intervalo de polling, um botão manual de "Atualizar
    // status" deixa o próprio cliente decidir quando checar de novo — mais
    // simples que um polling automático, e suficiente pra esse caso (o
    // cliente já recebe a confirmação visual da InfinitePay na hora do
    // pagamento, isso aqui é só o reflexo no nosso lado).
    setResultado(RESULTADO_INICIAL);
  }

  if (pedidoId == null) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <h1 className="text-2xl font-semibold">Pedido confirmado!</h1>
        <p className="mt-2 text-sm text-muted-foreground">Seu pedido foi recebido com sucesso.</p>
        <Link
          to="/"
          className="mt-6 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Voltar ao catálogo
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">Carregando pedido...</p>
      </div>
    );
  }

  if (resultado.erro) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-destructive">{resultado.erro}</p>
        <Link
          to="/meus-pedidos"
          className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Ver meus pedidos
        </Link>
      </div>
    );
  }

  const pedido = resultado.pedido;
  const pagamentoConfirmado = pedido.status !== "novo";

  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center">
      <h1 className="text-2xl font-semibold">
        {pagamentoConfirmado ? "Pagamento confirmado!" : "Pedido recebido!"}
      </h1>

      <div className="mt-3 flex items-center justify-center gap-2">
        <span className="text-sm text-muted-foreground">Pedido #{pedido.id}</span>
        <PedidoStatusBadge status={pedido.status} />
      </div>

      <p className="mt-4 text-sm text-muted-foreground">
        {pagamentoConfirmado
          ? "Recebemos a confirmação do seu pagamento."
          : "Estamos aguardando a confirmação do pagamento pela InfinitePay. Isso costuma levar só alguns instantes."}
      </p>

      <p className="mt-2 text-sm">
        Total: <span className="font-semibold">{formatarPreco(pedido.total)}</span>
      </p>

      {!pagamentoConfirmado && (
        <Button type="button" variant="outline" className="mt-6" onClick={handleAtualizar}>
          Atualizar status
        </Button>
      )}

      <div className="mt-6 flex flex-col gap-2">
        <Link
          to={`/meus-pedidos/${pedido.id}`}
          className="text-sm text-primary underline-offset-4 hover:underline"
        >
          Ver detalhes do pedido
        </Link>
        <Link to="/" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
          Voltar ao catálogo
        </Link>
      </div>
    </div>
  );
}

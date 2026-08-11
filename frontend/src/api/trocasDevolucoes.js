import api from "@/lib/axios";

// Segue a página até o fim (mesmo padrão de listarEnderecos()/
// listarCategorias(), não o de listarPedidos()): diferente do histórico de
// pedidos, que é ilimitado por natureza e por isso usa paginação real com
// controles Anterior/Próxima, o número de solicitações de troca/devolução
// de um usuário tende a ser pequeno — carregar tudo de uma vez numa lista
// simples é mais direto do que construir controles de paginação para um
// caso que raramente vai além de uma página.
export async function listarSolicitacoes() {
  let results = [];
  let url = "/trocas-devolucoes/";

  while (url) {
    const { data } = await api.get(url);
    results = results.concat(data.results);
    url = data.next;
  }

  return results;
}

export async function criarSolicitacao({ itemPedido, tipo, motivo }) {
  const { data } = await api.post("/trocas-devolucoes/", {
    item_pedido: itemPedido,
    tipo,
    motivo,
  });
  return data;
}

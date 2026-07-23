import api from "@/lib/axios";

// PedidoSerializer exposes `itens` as read_only, so there's no single endpoint
// that creates a Pedido together with its ItemPedido lines — the API only
// supports creating the Pedido first, then one POST /itens/ per cart line
// referencing the returned pedido.id.
export async function criarPedido() {
  const { data } = await api.post("/pedidos/", {});
  return data;
}

export async function criarItemPedido({ pedido, variacao, quantidade }) {
  const { data } = await api.post("/itens/", { pedido, variacao, quantidade });
  return data;
}

export async function deletarPedido(id) {
  await api.delete(`/pedidos/${id}/`);
}

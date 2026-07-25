import api from "@/lib/axios";

// PedidoSerializer exposes `itens` as read_only, so there's no single endpoint
// that creates a Pedido together with its ItemPedido lines — the API only
// supports creating the Pedido first, then one POST /itens/ per cart line
// referencing the returned pedido.id.
export async function criarPedido({ endereco } = {}) {
  const { data } = await api.post("/pedidos/", endereco ? { endereco } : {});
  return data;
}

export async function criarItemPedido({ pedido, variacao, quantidade }) {
  const { data } = await api.post("/itens/", { pedido, variacao, quantidade });
  return data;
}

export async function deletarPedido(id) {
  await api.delete(`/pedidos/${id}/`);
}

// Diferente de listarCategorias()/listarMarcas() (que seguem `next` até o
// fim), o histórico de pedidos de um usuário cresce indefinidamente, então
// aqui a paginação é real — a página pedida vai direto pro backend e a UI
// mostra controles Anterior/Próxima, no mesmo padrão de listarProdutos().
export async function listarPedidos({ page } = {}) {
  const params = {};
  if (page) params.page = page;

  const { data } = await api.get("/pedidos/", { params });
  return data;
}

export async function buscarPedido(id) {
  const { data } = await api.get(`/pedidos/${id}/`);
  return data;
}

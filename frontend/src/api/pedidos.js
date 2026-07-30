import api from "@/lib/axios";

// PedidoSerializer accepts a write-only `itens_criacao` list alongside the
// read-only `itens`, so a single POST /pedidos/ creates the Pedido and every
// ItemPedido line together inside one backend DB transaction (see
// PedidoViewSet.perform_create() and CLAUDE.md) — no partial/orphaned Pedido
// possible if one line fails (e.g. insufficient stock on line 2), unlike the
// old "create empty Pedido, then loop POST /itens/" flow this replaced.
// `itens` is optional and omitted entirely (not sent as `[]`) when not
// passed, so a bare `criarPedido({ endereco })` still creates an empty
// Pedido exactly like before — that path is still exercised by the backend
// itself (e.g. the Django admin) and intentionally still supported.
// `frete` is the whole option object returned by calcularFrete() ({id, nome,
// transportadora, preco, prazo_dias}) — sent as-is under `frete_selecionado`,
// PedidoSerializer only reads the four sub-fields it actually freezes onto
// the Pedido (see CLAUDE.md). Optional and omitted entirely when not passed,
// same as endereco/itens — Checkout.jsx doesn't block on a failed/unselected
// SuperFrete quote, so a Pedido can legitimately be created with no freight.
export async function criarPedido({ endereco, itens, frete } = {}) {
  const payload = {};
  if (endereco) payload.endereco = endereco;
  if (itens && itens.length > 0) {
    payload.itens_criacao = itens.map(({ variacao, quantidade }) => ({ variacao, quantidade }));
  }
  if (frete) payload.frete_selecionado = frete;

  const { data } = await api.post("/pedidos/", payload);
  return data;
}

// Unused by the UI now that criarPedido() creates every line atomically, but
// POST /itens/ itself is still live (and still needed for it) — kept as a
// direct binding in case a future feature needs to add a single line to an
// already-existing Pedido (this endpoint doesn't require the Pedido to be
// empty/new).
export async function criarItemPedido({ pedido, variacao, quantidade }) {
  const { data } = await api.post("/itens/", { pedido, variacao, quantidade });
  return data;
}

// Unused by Checkout.jsx now that order creation is atomic (no more orphaned
// Pedido to roll back on a mid-loop failure) — kept as a direct binding
// since DELETE /pedidos/{id}/ is still a real, supported endpoint and this
// is likely useful for a future "cancelar pedido" feature.
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

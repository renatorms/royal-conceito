import api from "@/lib/axios";

// POST /frete/calcular/ is public (AllowAny — see CLAUDE.md), so this call
// works even for an anonymous visitor browsing the cart; withCredentials
// (set globally on `api`) is harmless here since no cookie is required.
// `itens` mirrors criarPedido()'s shape: { variacao, quantidade } pairs, not
// the cart's own item shape (variacaoId) — mapped by the caller.
export async function calcularFrete(cepDestino, itens) {
  const { data } = await api.post("/frete/calcular/", {
    cep_destino: cepDestino,
    itens: itens.map(({ variacao, quantidade }) => ({ variacao, quantidade })),
  });
  return data;
}

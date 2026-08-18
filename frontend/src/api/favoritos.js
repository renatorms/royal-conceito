import api from "@/lib/axios";

export async function listarFavoritos() {
  let results = [];
  let url = "/favoritos/";

  while (url) {
    const { data } = await api.get(url);
    results = results.concat(data.results);
    url = data.next;
  }

  return results;
}

export async function criarFavorito(produtoId) {
  const { data } = await api.post("/favoritos/", { produto_id: produtoId });
  return data;
}

export async function deletarFavorito(id) {
  await api.delete(`/favoritos/${id}/`);
}

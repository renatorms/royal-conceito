import api from "@/lib/axios";

export async function listarEnderecos() {
  let results = [];
  let url = "/enderecos/";

  while (url) {
    const { data } = await api.get(url);
    results = results.concat(data.results);
    url = data.next;
  }

  return results;
}

export async function criarEndereco(dados) {
  const { data } = await api.post("/enderecos/", dados);
  return data;
}

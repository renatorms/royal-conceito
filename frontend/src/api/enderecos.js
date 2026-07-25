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

// PATCH (não PUT): EnderecoViewSet não sobrescreve `usuario` num update como
// faz em perform_create(), e o campo é obrigatório no serializer — um PUT
// completo exigiria reenviar `usuario` no payload. Um PATCH parcial só valida
// os campos enviados, então dá pra atualizar sem tocar em `usuario`.
export async function atualizarEndereco(id, dados) {
  const { data } = await api.patch(`/enderecos/${id}/`, dados);
  return data;
}

export async function deletarEndereco(id) {
  await api.delete(`/enderecos/${id}/`);
}

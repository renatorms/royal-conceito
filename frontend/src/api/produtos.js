import api from "@/lib/axios";

async function listarTodasPaginas(endpoint) {
  let results = [];
  let url = endpoint;

  while (url) {
    const { data } = await api.get(url);
    results = results.concat(data.results);
    url = data.next;
  }

  return results;
}

export async function listarProdutos({
  categoria,
  marca,
  search,
  ordering,
  page,
  pageSize,
  emOutlet,
} = {}) {
  const params = {};
  if (categoria) params.categoria = categoria;
  if (marca) params.marca = marca;
  if (search) params.search = search;
  if (ordering) params.ordering = ordering;
  if (page) params.page = page;
  if (pageSize) params.page_size = pageSize;
  if (emOutlet) params.em_outlet = "true";

  const { data } = await api.get("/produtos/", { params });
  return data;
}

export async function buscarProduto(id) {
  const { data } = await api.get(`/produtos/${id}/`);
  return data;
}

export async function listarCategorias() {
  return listarTodasPaginas("/categorias/");
}

export async function listarMarcas() {
  return listarTodasPaginas("/marcas/");
}

export async function buscarMenuCategorias() {
  const { data } = await api.get("/menu/categorias/");
  return data;
}

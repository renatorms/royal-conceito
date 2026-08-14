import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { LayoutGridIcon, ListIcon } from "lucide-react";
import { listarProdutos } from "@/api/produtos";
import { ProdutoCard } from "@/components/ProdutoCard";
import { ProdutoCardLista } from "@/components/ProdutoCardLista";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PADRAO = "padrao";
const PAGE_SIZE_PADRAO = 10;
// Mantido em sincronia com ProdutoPagination.max_page_size (backend,
// produtos/pagination.py) — só o valor máximo (50) precisa bater; o
// backend recusa qualquer page_size acima disso, então oferecer uma opção
// maior aqui não adiantaria nada.
const OPCOES_PAGE_SIZE = [10, 20, 50];

const VIEW_PADRAO = "grid";
const CHAVE_VIEW_LOCALSTORAGE = "catalogo_view";

const RESULTADO_INICIAL = {
  chave: null,
  produtos: [],
  count: 0,
  next: null,
  previous: null,
  erro: null,
};

export default function Catalogo() {
  const [searchParams, setSearchParams] = useSearchParams();

  const categoria = searchParams.get("categoria") || "";
  const marca = searchParams.get("marca") || "";
  const search = searchParams.get("search") || "";
  const ordering = searchParams.get("ordering") || "";
  const emOutlet = searchParams.get("em_outlet") === "true";
  const page = Number(searchParams.get("page")) || 1;
  const pageSizeParam = Number(searchParams.get("page_size"));
  const pageSize = OPCOES_PAGE_SIZE.includes(pageSizeParam) ? pageSizeParam : PAGE_SIZE_PADRAO;

  // ?view= na URL manda quando presente; sem ele, cai pro que foi salvo no
  // localStorage numa visita anterior (persistência entre sessões, não só
  // dentro da mesma navegação); sem nenhum dos dois, grade é o padrão.
  const viewParam = searchParams.get("view");
  const view =
    viewParam === "grid" || viewParam === "list"
      ? viewParam
      : localStorage.getItem(CHAVE_VIEW_LOCALSTORAGE) || VIEW_PADRAO;

  const [resultado, setResultado] = useState(RESULTADO_INICIAL);

  const chaveAtual = JSON.stringify({
    categoria,
    marca,
    search,
    ordering,
    emOutlet,
    page,
    pageSize,
  });
  const isLoading = resultado.chave !== chaveAtual;

  useEffect(() => {
    let ignore = false;

    listarProdutos({ categoria, marca, search, ordering, page, pageSize, emOutlet })
      .then((data) => {
        if (ignore) return;
        setResultado({
          chave: chaveAtual,
          produtos: data.results,
          count: data.count,
          next: data.next,
          previous: data.previous,
          erro: null,
        });
      })
      .catch(() => {
        if (ignore) return;
        setResultado({
          chave: chaveAtual,
          produtos: [],
          count: 0,
          next: null,
          previous: null,
          erro: "Não foi possível carregar os produtos.",
        });
      });

    return () => {
      ignore = true;
    };
  }, [categoria, marca, search, ordering, emOutlet, page, pageSize, chaveAtual]);

  function atualizarFiltro(chave, valor) {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      if (valor && valor !== PADRAO) {
        nextParams.set(chave, valor);
      } else {
        nextParams.delete(chave);
      }
      nextParams.delete("page");
      return nextParams;
    });
  }

  function irParaPagina(novaPagina) {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      if (novaPagina > 1) {
        nextParams.set("page", String(novaPagina));
      } else {
        nextParams.delete("page");
      }
      return nextParams;
    });
  }

  function alterarPageSize(valor) {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      const novoPageSize = Number(valor);
      if (novoPageSize && novoPageSize !== PAGE_SIZE_PADRAO) {
        nextParams.set("page_size", String(novoPageSize));
      } else {
        nextParams.delete("page_size");
      }
      nextParams.delete("page");
      return nextParams;
    });
  }

  function alterarView(novaView) {
    localStorage.setItem(CHAVE_VIEW_LOCALSTORAGE, novaView);
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      if (novaView !== VIEW_PADRAO) {
        nextParams.set("view", novaView);
      } else {
        nextParams.delete("view");
      }
      return nextParams;
    });
    // Não mexe em "page": trocar o modo de visualização não é um filtro,
    // continua mostrando a mesma página de resultados já carregada.
  }

  function limparFiltros() {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams();
      // page_size e view são preferências de exibição, não filtros — mantidas.
      const pageSizeAtual = params.get("page_size");
      if (pageSizeAtual) nextParams.set("page_size", pageSizeAtual);
      const viewAtual = params.get("view");
      if (viewAtual) nextParams.set("view", viewAtual);
      return nextParams;
    });
  }

  const totalPaginas = Math.max(1, Math.ceil(resultado.count / pageSize));
  const temFiltrosAtivos = Boolean(categoria || marca || search || ordering || emOutlet);

  const orderingItems = [
    { value: PADRAO, label: "Padrão" },
    { value: "-criado_em", label: "Mais recentes" },
    { value: "preco", label: "Menor preço" },
    { value: "-preco", label: "Maior preço" },
    { value: "nome", label: "Nome (A-Z)" },
    { value: "-nome", label: "Nome (Z-A)" },
  ];

  const pageSizeItems = OPCOES_PAGE_SIZE.map((valor) => ({
    value: String(valor),
    label: `${valor} por página`,
  }));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Busca/categoria/marca são cobertos pelo HeaderNav (busca, e
          navegação Calçados/Roupas/Acessórios/Marcas/Outlet) — só
          ordenação e o modo de visualização, que não existem lá, têm
          controle aqui. */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Catálogo</h1>

        <div className="flex flex-wrap items-center gap-3">
          <Select
            items={pageSizeItems}
            value={String(pageSize)}
            onValueChange={alterarPageSize}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Por página" />
            </SelectTrigger>
            <SelectContent>
              {pageSizeItems.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            items={orderingItems}
            value={ordering || PADRAO}
            onValueChange={(v) => atualizarFiltro("ordering", v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Ordenar" />
            </SelectTrigger>
            <SelectContent>
              {orderingItems.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant={view === "grid" ? "secondary" : "ghost"}
              size="icon-sm"
              aria-label="Ver em grade"
              aria-pressed={view === "grid"}
              onClick={() => alterarView("grid")}
            >
              <LayoutGridIcon />
            </Button>
            <Button
              type="button"
              variant={view === "list" ? "secondary" : "ghost"}
              size="icon-sm"
              aria-label="Ver em lista"
              aria-pressed={view === "list"}
              onClick={() => alterarView("list")}
            >
              <ListIcon />
            </Button>
          </div>
        </div>
      </div>

      {resultado.erro ? (
        <p className="text-sm text-destructive">{resultado.erro}</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando produtos...</p>
      ) : resultado.produtos.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-sm text-muted-foreground">
            {temFiltrosAtivos
              ? "Nenhum produto encontrado para os filtros selecionados."
              : "Nenhum produto encontrado."}
          </p>
          {temFiltrosAtivos && (
            <Button type="button" variant="outline" size="sm" onClick={limparFiltros}>
              Limpar filtros
            </Button>
          )}
        </div>
      ) : (
        <>
          <p className="mb-4 text-sm text-muted-foreground">
            {resultado.count} {resultado.count === 1 ? "produto encontrado" : "produtos encontrados"}
          </p>

          {view === "list" ? (
            <div className="flex flex-col gap-3">
              {resultado.produtos.map((produto) => (
                <ProdutoCardLista key={produto.id} produto={produto} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {resultado.produtos.map((produto) => (
                <ProdutoCard key={produto.id} produto={produto} />
              ))}
            </div>
          )}
        </>
      )}

      {resultado.count > 0 && (
        <div className="mt-8 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={!resultado.previous}
            onClick={() => irParaPagina(page - 1)}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPaginas}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!resultado.next}
            onClick={() => irParaPagina(page + 1)}
          >
            Próxima
          </Button>
        </div>
      )}
    </div>
  );
}

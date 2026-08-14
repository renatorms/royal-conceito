import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listarProdutos } from "@/api/produtos";
import { ProdutoCard } from "@/components/ProdutoCard";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PADRAO = "padrao";
const PAGE_SIZE_PADRAO = 12;
// Mantido em sincronia com ProdutoPagination.max_page_size (backend,
// produtos/pagination.py) — o valor máximo (50) só precisa ser >= o maior
// valor aqui (48); o backend recusa qualquer page_size acima do próprio
// limite, então oferecer uma opção maior aqui não adiantaria nada. 12 é
// múltiplo de 2/3/4 (as três larguras de grid usadas: grid-cols-2 mobile,
// sm:grid-cols-3, lg:grid-cols-4), então nenhuma delas fica com a última
// linha incompleta.
const OPCOES_PAGE_SIZE = [12, 24, 48];

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

  function limparFiltros() {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams();
      // page_size é preferência de exibição, não filtro — mantida.
      const pageSizeAtual = params.get("page_size");
      if (pageSizeAtual) nextParams.set("page_size", pageSizeAtual);
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
          ordenação, que não existe lá, tem controle aqui. */}
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

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {resultado.produtos.map((produto) => (
              <ProdutoCard key={produto.id} produto={produto} />
            ))}
          </div>
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

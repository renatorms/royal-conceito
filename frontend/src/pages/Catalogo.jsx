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
const PAGE_SIZE = 10;

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
  const page = Number(searchParams.get("page")) || 1;

  const [resultado, setResultado] = useState(RESULTADO_INICIAL);

  const chaveAtual = JSON.stringify({ categoria, marca, search, ordering, page });
  const isLoading = resultado.chave !== chaveAtual;

  useEffect(() => {
    let ignore = false;

    listarProdutos({ categoria, marca, search, ordering, page })
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
  }, [categoria, marca, search, ordering, page, chaveAtual]);

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

  const totalPaginas = Math.max(1, Math.ceil(resultado.count / PAGE_SIZE));

  const orderingItems = [
    { value: PADRAO, label: "Padrão" },
    { value: "preco", label: "Menor preço" },
    { value: "-preco", label: "Maior preço" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Busca/categoria/marca são cobertos pelo HeaderNav (busca, e
          navegação Tênis/Roupas/Acessórios/Marcas) — só a ordenação, que
          não existe lá e é específica desta visualização em lista, tem
          controle aqui. Título e ordenação dividem uma linha em vez de
          duas (era um `<h1>` + uma barra de filtros de 4 campos abaixo)
          já que agora só há um controle a mostrar. */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Catálogo</h1>

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

      {resultado.erro ? (
        <p className="text-sm text-destructive">{resultado.erro}</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando produtos...</p>
      ) : resultado.produtos.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhum produto encontrado.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {resultado.produtos.map((produto) => (
            <ProdutoCard key={produto.id} produto={produto} />
          ))}
        </div>
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

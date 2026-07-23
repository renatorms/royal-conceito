import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listarProdutos, listarCategorias, listarMarcas } from "@/api/produtos";
import { ProdutoCard } from "@/components/ProdutoCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TODOS = "todos";
const PADRAO = "padrao";
const SEARCH_DEBOUNCE_MS = 400;
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

  const [searchInput, setSearchInput] = useState(search);
  const [lastUrlSearch, setLastUrlSearch] = useState(search);
  const [categorias, setCategorias] = useState([]);
  const [marcas, setMarcas] = useState([]);
  const [resultado, setResultado] = useState(RESULTADO_INICIAL);

  const chaveAtual = JSON.stringify({ categoria, marca, search, ordering, page });
  const isLoading = resultado.chave !== chaveAtual;

  // Keeps the input in sync when `search` changes from outside a keystroke
  // (e.g. browser back/forward) — updating state during render, per
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  if (search !== lastUrlSearch) {
    setLastUrlSearch(search);
    setSearchInput(search);
  }

  useEffect(() => {
    listarCategorias().then(setCategorias).catch(() => {});
    listarMarcas().then(setMarcas).catch(() => {});
  }, []);

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

  useEffect(() => {
    const handle = setTimeout(() => {
      if (searchInput === search) return;

      setSearchParams((params) => {
        const nextParams = new URLSearchParams(params);
        if (searchInput) {
          nextParams.set("search", searchInput);
        } else {
          nextParams.delete("search");
        }
        nextParams.delete("page");
        return nextParams;
      });
    }, SEARCH_DEBOUNCE_MS);

    return () => clearTimeout(handle);
  }, [searchInput, search, setSearchParams]);

  function atualizarFiltro(chave, valor) {
    setSearchParams((params) => {
      const nextParams = new URLSearchParams(params);
      if (valor && valor !== TODOS && valor !== PADRAO) {
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

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Catálogo</h1>

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <Input
          placeholder="Buscar produtos..."
          className="w-full max-w-xs"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />

        <Select value={categoria || TODOS} onValueChange={(v) => atualizarFiltro("categoria", v)}>
          <SelectTrigger>
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TODOS}>Todas as categorias</SelectItem>
            {categorias.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={marca || TODOS} onValueChange={(v) => atualizarFiltro("marca", v)}>
          <SelectTrigger>
            <SelectValue placeholder="Marca" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TODOS}>Todas as marcas</SelectItem>
            {marcas.map((m) => (
              <SelectItem key={m.id} value={String(m.id)}>
                {m.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={ordering || PADRAO} onValueChange={(v) => atualizarFiltro("ordering", v)}>
          <SelectTrigger>
            <SelectValue placeholder="Ordenar" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={PADRAO}>Padrão</SelectItem>
            <SelectItem value="preco">Menor preço</SelectItem>
            <SelectItem value="-preco">Maior preço</SelectItem>
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

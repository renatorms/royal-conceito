import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { SearchIcon } from "lucide-react";
import { buscarMenuCategorias, listarMarcas } from "@/api/produtos";
import { Input } from "@/components/ui/input";
import { NavDropdown } from "@/components/NavDropdown";

// Categoria has no "tipo"/"grupo" field to tell clothing apart from
// footwear/accessories — the schema only has `nome`. Matching by name here
// is a deliberate, documented limitation (see CLAUDE.md), not an
// oversight: the real fix would be adding a `tipo` field to Categoria,
// which is a data-model decision out of scope for this Header redesign
// (same reasoning CLAUDE.md already uses for leaving "Promoções" out — see
// there). If a Categoria is ever renamed, or a new one is added under a
// name not listed in the group it logically belongs to, that nav item
// simply won't pick it up until the matching list below is updated by
// hand — this has already happened once for real (see CLAUDE.md): five
// real categorias the user created by hand through the Admin —
// "Conjuntos", "Jeans", "Polos", "Bermudas Elastano", "Sandálias" — went
// unrecognized elsewhere in the backend (`aplicar_variacoes_padrao.py`)
// until their names were added to the matching list there too.
//
// Three groups today, each backing its own NavDropdown mega menu below
// (same shape: a grid of categoria → marcas, via `PainelCategoriasMarcas`).
// "Tamanho único" categorias (Bonés, Acessórios) and "roupa" categorias
// both use TAMANHOS_ROUPA/TAMANHO_UNICO server-side (see CATEGORIAS_CONFIG,
// `seed_produtos.py`) — that backend grouping is the actual source of
// truth these three lists mirror by hand on the frontend, not something
// derived automatically from it (no endpoint exposes it as data yet).
const NOMES_CATEGORIAS_ROUPA = [
  "Camisetas",
  "Bermudas",
  "Calças",
  "Jaquetas/Moletons",
  "Polos",
  "Bermudas Elastano",
  "Jeans",
  "Conjuntos",
];
const NOMES_CATEGORIAS_CALCADO = ["Tênis", "Sandálias"];
const NOMES_CATEGORIAS_ACESSORIO = ["Acessórios", "Bonés"];

const CLASSE_LINK_PAINEL =
  "text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline";

// Shared panel content for every categoria-grouped NavDropdown below
// (Calçados/Roupas/Acessórios) — extracted once all three needed the exact
// same "grid of categoria → marcas" shape (previously only "Roupas" had
// this; duplicating it two more times verbatim wasn't worth it). "Marcas"
// still renders its own flat list further down, not this: it has no
// categoria dimension to group by.
function PainelCategoriasMarcas({ categorias }) {
  return (
    <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
      {categorias.map((categoria) => (
        <div key={categoria.id}>
          <p className="mb-2 border-b border-primary/30 pb-1 text-sm font-semibold text-foreground">
            {categoria.nome}
          </p>
          <ul className="space-y-1.5">
            {categoria.marcas.map((marca) => (
              <li key={marca.id}>
                <Link
                  to={`/?categoria=${categoria.id}&marca=${marca.id}`}
                  className={CLASSE_LINK_PAINEL}
                >
                  {marca.nome}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function HeaderNav() {
  const [menuCategorias, setMenuCategorias] = useState([]);
  const [marcas, setMarcas] = useState([]);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    buscarMenuCategorias().then(setMenuCategorias).catch(() => {});
    listarMarcas().then(setMarcas).catch(() => {});
  }, []);

  const termoUrl = searchParams.get("search") || "";
  const [termoBusca, setTermoBusca] = useState(termoUrl);
  const [ultimoTermoUrl, setUltimoTermoUrl] = useState(termoUrl);

  // Keeps the field in sync when `search` changes from outside a keystroke
  // here (e.g. clicking a filter link elsewhere, or landing directly on a
  // /?search=... URL) — updated during render, same pattern (and same
  // react-hooks/set-state-in-effect reasoning) as Catalogo.jsx's own
  // search input.
  if (termoUrl !== ultimoTermoUrl) {
    setUltimoTermoUrl(termoUrl);
    setTermoBusca(termoUrl);
  }

  function handleBuscar(e) {
    e.preventDefault();
    const termo = termoBusca.trim();
    navigate(termo ? `/?search=${encodeURIComponent(termo)}` : "/");
  }

  // Calçados/Roupas/Acessórios (all three mega menus below) are derived
  // from the SAME GET /api/menu/categorias/ call — no separate
  // GET /categorias/ request just to resolve their ids, since this data
  // already has them. Trade-off, inherited from that endpoint's own
  // design (see CLAUDE.md): it only lists a Categoria that currently has
  // at least one Produto with a Marca set, so a categoria (and, if it's
  // the only one left in its group, the whole nav item) quietly stops
  // rendering if its catalog/stock ever drops to zero, rather than
  // showing a dead link into an empty view.
  const categoriasCalcado = menuCategorias.filter((c) =>
    NOMES_CATEGORIAS_CALCADO.includes(c.nome)
  );
  const categoriasRoupa = menuCategorias.filter((c) =>
    NOMES_CATEGORIAS_ROUPA.includes(c.nome)
  );
  const categoriasAcessorio = menuCategorias.filter((c) =>
    NOMES_CATEGORIAS_ACESSORIO.includes(c.nome)
  );

  return (
    <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
      {categoriasCalcado.length > 0 && (
        <NavDropdown label="Calçados">
          <PainelCategoriasMarcas categorias={categoriasCalcado} />
        </NavDropdown>
      )}

      {categoriasRoupa.length > 0 && (
        <NavDropdown label="Roupas">
          <PainelCategoriasMarcas categorias={categoriasRoupa} />
        </NavDropdown>
      )}

      {categoriasAcessorio.length > 0 && (
        <NavDropdown label="Acessórios">
          <PainelCategoriasMarcas categorias={categoriasAcessorio} />
        </NavDropdown>
      )}

      {marcas.length > 0 && (
        // A flat list, not a multi-column mega menu grid like "Roupas":
        // Marcas is a single dimension (no categoria to group by), so a
        // plain vertical list inside the same NavDropdown shell is simpler
        // and reads better than forcing an arbitrary column split.
        // Deliberately every registered Marca (listarMarcas(), unfiltered)
        // rather than only marcas with products (unlike Calçados/Roupas/
        // Acessórios above) — a Marca with no stock right now still links
        // to a valid (if momentarily empty) filtered catalog view.
        <NavDropdown label="Marcas">
          <ul className="max-h-[60vh] space-y-1.5 overflow-y-auto pr-1">
            {marcas.map((marca) => (
              <li key={marca.id}>
                <Link to={`/?marca=${marca.id}`} className={CLASSE_LINK_PAINEL}>
                  {marca.nome}
                </Link>
              </li>
            ))}
          </ul>
        </NavDropdown>
      )}

      <form onSubmit={handleBuscar} className="flex items-center gap-1">
        <Input
          type="search"
          placeholder="Buscar produtos..."
          value={termoBusca}
          onChange={(e) => setTermoBusca(e.target.value)}
          className="h-8 w-36 sm:w-44"
        />
        <button
          type="submit"
          aria-label="Buscar"
          className="flex size-8 shrink-0 items-center justify-center text-muted-foreground hover:text-primary"
        >
          <SearchIcon className="size-4" />
        </button>
      </form>
    </nav>
  );
}

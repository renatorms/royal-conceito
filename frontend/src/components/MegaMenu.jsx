import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDownIcon } from "lucide-react";
import { buscarMenuCategorias } from "@/api/produtos";

// Categoria (coluna) → Marcas disponíveis nela (links), não Marca → Modelo
// como no padrão visual de referência: Produto não tem um campo de
// "linha/modelo" (ex: "Dunk", "Blazer") hoje, só marca + categoria — ver
// CLAUDE.md para a decisão completa e se isso deve ser reconsiderado no
// futuro.
export function MegaMenu() {
  const [menu, setMenu] = useState([]);

  useEffect(() => {
    buscarMenuCategorias()
      .then(setMenu)
      .catch(() => {});
  }, []);

  // Nenhuma Categoria com produto+marca cadastrados ainda (banco vazio, ou
  // a chamada falhou) — melhor não mostrar o gatilho "Categorias" do que
  // mostrar um menu que abre vazio.
  if (menu.length === 0) return null;

  return (
    <>
      {/* Desktop: expande no hover (ou foco via teclado), painel
          multi-coluna. Sem estado em React — group-hover/group-focus-within
          do Tailwind cobre abrir/fechar; `hidden` (não opacity/visibility)
          enquanto fechado tira os links do painel da ordem de tab. */}
      <div className="group relative hidden md:block">
        <Link
          to="/"
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
        >
          Categorias
          <ChevronDownIcon className="size-3.5 transition-transform group-hover:rotate-180 group-focus-within:rotate-180" />
        </Link>

        <div className="absolute left-0 top-full z-50 hidden w-max min-w-[560px] max-w-3xl rounded-b-md border border-t-0 border-border bg-popover p-6 text-popover-foreground shadow-lg group-hover:block group-focus-within:block">
          <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
            {menu.map((categoria) => (
              <div key={categoria.id}>
                <p className="mb-2 border-b border-primary/30 pb-1 text-sm font-semibold text-foreground">
                  {categoria.nome}
                </p>
                <ul className="space-y-1.5">
                  {categoria.marcas.map((marca) => (
                    <li key={marca.id}>
                      <Link
                        to={`/?categoria=${categoria.id}&marca=${marca.id}`}
                        className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline"
                      >
                        {marca.nome}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile: hover não existe em touch — <details>/<summary> nativo dá
          um accordion tap-to-expand sem precisar de estado em React nem de
          um menu mobile completo (drawer, overlay, etc.), que não é
          necessário para o que foi pedido aqui. */}
      <details className="group md:hidden">
        <summary className="flex cursor-pointer list-none items-center gap-1 text-muted-foreground hover:text-foreground [&::-webkit-details-marker]:hidden">
          Categorias
          <ChevronDownIcon className="size-3.5 transition-transform group-open:rotate-180" />
        </summary>
        <div className="mt-3 space-y-4 border-t border-border pt-3">
          {menu.map((categoria) => (
            <div key={categoria.id}>
              <p className="mb-1.5 text-sm font-semibold text-foreground">
                {categoria.nome}
              </p>
              <ul className="space-y-1.5 pl-2">
                {categoria.marcas.map((marca) => (
                  <li key={marca.id}>
                    <Link
                      to={`/?categoria=${categoria.id}&marca=${marca.id}`}
                      className="text-sm text-muted-foreground hover:text-primary"
                    >
                      {marca.nome}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </details>
    </>
  );
}

import { Link, useNavigate } from "react-router-dom";
import { ShoppingCartIcon, UserIcon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/contexts/CartContext";
import { Button } from "@/components/ui/button";
import { HeaderNav } from "@/components/HeaderNav";
import logoRoyalConceito from "@/assets/logoroyalconceito.png";

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { totalItens } = useCart();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    // Classic e-commerce 3-column layout: logo (auto-width, left) — nav
    // (1fr, truly centered regardless of how wide the logo/actions columns
    // are — a plain flex `justify-between` would only visually center the
    // middle item if both sides happened to be equal width) — actions
    // (auto-width, right). The right-hand nav content itself (Meus
    // Pedidos/Meus Endereços/carrinho/login-or-logout) is unchanged from
    // before this redesign, just relocated into its own grid column; only
    // the old catch-all "Categorias" MegaMenu was replaced, by `HeaderNav`
    // — see CLAUDE.md for the full redesign.
    <header className="grid grid-cols-[auto_1fr_auto] items-center gap-4 border-b border-border px-4 py-4">
      <Link to="/" className="shrink-0">
        <img
          src={logoRoyalConceito}
          alt="Royal Conceito"
          className="h-16 w-auto object-contain"
        />
      </Link>

      <HeaderNav />

      <nav className="flex items-center justify-end gap-3 text-sm">
        <Link to="/meus-pedidos" className="text-muted-foreground hover:text-foreground">
          Meus Pedidos
        </Link>

        <Link to="/meus-enderecos" className="text-muted-foreground hover:text-foreground">
          Meus Endereços
        </Link>

        <Link
          to="/carrinho"
          aria-label="Carrinho"
          className="relative flex items-center text-muted-foreground hover:text-foreground"
        >
          <ShoppingCartIcon className="size-5" />
          {totalItens > 0 && (
            <span className="absolute -top-2 -right-2 flex size-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
              {totalItens}
            </span>
          )}
        </Link>

        {isLoading ? null : isAuthenticated ? (
          <>
            {/* Desktop: same hover/focus-reveal idiom as NavDropdown.jsx
                (group-hover/group-focus-within, `hidden` keeps the panel
                out of the tab order while closed) — but not NavDropdown
                itself, whose panel is sized/anchored for a wide, centered
                mega-menu of links (min-w-[220px], p-6, centered under the
                trigger). This is a compact 2-line account menu that
                belongs anchored to the right edge — it's the header's
                last item, so centering it could push the panel off-screen
                — and doesn't need that much width or padding. Same
                interaction mechanism, purpose-built sizing instead of a
                forced reuse. */}
            <div className="group relative hidden md:block">
              <button
                type="button"
                aria-haspopup="true"
                aria-label={`Conta de ${user.username}`}
                className="flex items-center text-muted-foreground hover:text-foreground"
              >
                <UserIcon className="size-5" />
              </button>

              <div className="absolute right-0 top-full z-50 hidden min-w-[160px] rounded-md border border-border bg-popover p-3 text-popover-foreground shadow-lg group-hover:block group-focus-within:block">
                <p className="truncate px-1 pb-2 text-xs text-muted-foreground">
                  {user.username}
                </p>
                <Link
                  to="/perfil"
                  className="mb-2 block text-sm text-muted-foreground hover:text-foreground"
                >
                  Perfil
                </Link>
                <Button variant="outline" size="sm" className="w-full" onClick={handleLogout}>
                  Sair
                </Button>
              </div>
            </div>

            {/* Mobile: hover doesn't exist on touch — native
                <details>/<summary> tap-to-expand, same mechanism
                NavDropdown.jsx uses for Roupas/Marcas on mobile. Unlike
                NavDropdown's mobile panel (which renders inline and pushes
                the rest of its row down — fine there, since it lives in a
                nav row that already wraps freely), this one is absolutely
                positioned as an overlay instead: it's one fixed-size icon
                among several others in the header's actions row, and
                letting it grow inline would shove the cart icon/links
                sideways every time it opens. */}
            <details className="relative md:hidden">
              <summary
                aria-label={`Conta de ${user.username}`}
                className="flex cursor-pointer list-none items-center text-muted-foreground hover:text-foreground [&::-webkit-details-marker]:hidden"
              >
                <UserIcon className="size-5" />
              </summary>
              <div className="absolute right-0 top-full z-50 mt-2 min-w-[160px] rounded-md border border-border bg-popover p-3 text-popover-foreground shadow-lg">
                <p className="truncate px-1 pb-2 text-xs text-muted-foreground">
                  {user.username}
                </p>
                <Link
                  to="/perfil"
                  className="mb-2 block text-sm text-muted-foreground hover:text-foreground"
                >
                  Perfil
                </Link>
                <Button variant="outline" size="sm" className="w-full" onClick={handleLogout}>
                  Sair
                </Button>
              </div>
            </details>
          </>
        ) : (
          <Button variant="outline" size="sm" render={<Link to="/login" />}>
            Login
          </Button>
        )}
      </nav>
    </header>
  );
}

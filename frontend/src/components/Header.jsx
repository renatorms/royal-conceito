import { Link } from "react-router-dom";
import { ShoppingCartIcon, UserIcon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/contexts/CartContext";
import { Button } from "@/components/ui/button";
import { HeaderNav } from "@/components/HeaderNav";
import logoRoyalConceito from "@/assets/logoroyalconceito.png";

export function Header() {
  const { isAuthenticated, isLoading } = useAuth();
  const { totalItens } = useCart();

  return (
    // Classic e-commerce 3-column layout: logo (auto-width, left) — nav
    // (1fr, truly centered regardless of how wide the logo/actions columns
    // are — a plain flex `justify-between` would only visually center the
    // middle item if both sides happened to be equal width) — actions
    // (auto-width, right). The right-hand actions cluster is just
    // carrinho/account-icon-or-login — "Meus Pedidos"/"Meus Endereços"
    // moved here briefly but were removed once they became redundant with
    // the "Minha Conta" hub (MinhaConta.jsx), which already lists both.
    <header className="grid grid-cols-[auto_1fr_auto] items-center gap-4 border-b border-border px-4 py-3">
      <div className="relative h-12 w-36 shrink-0">
        <Link to="/" className="absolute inset-0 flex items-center">
          <img
            src={logoRoyalConceito}
            alt="Royal Conceito"
            className="absolute left-0 top-1/2 h-20 w-auto -translate-y-1/2 object-contain"
          />
        </Link>
      </div>

      <HeaderNav />

      <nav className="flex items-center justify-end gap-3 text-sm">
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
          // Restructured 10/08 — was a hover/tap dropdown (username + a
          // "Perfil" link + a "Sair" button, two separate desktop/mobile
          // blocks with different interaction mechanisms). "Minha Conta"
          // is now its own hub page (MinhaConta.jsx) with all of that as
          // real, clickable rows — including "Sair" itself, now an action
          // *inside* that page rather than something reachable only from
          // this header dropdown — so the icon here has nothing left to
          // reveal on hover/tap; it's just a destination, same idiom as
          // the cart icon Link right above it (no NavDropdown, no
          // desktop/mobile split needed either).
          <Link
            to="/minha-conta"
            aria-label="Minha Conta"
            className="flex items-center text-muted-foreground hover:text-foreground"
          >
            <UserIcon className="size-5" />
          </Link>
        ) : (
          <Button variant="outline" size="sm" render={<Link to="/login" />}>
            Login
          </Button>
        )}
      </nav>
    </header>
  );
}

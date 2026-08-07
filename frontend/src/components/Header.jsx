import { Link, useNavigate } from "react-router-dom";
import { ShoppingCartIcon } from "lucide-react";
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
            <span className="text-muted-foreground">{user.username}</span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Sair
            </Button>
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

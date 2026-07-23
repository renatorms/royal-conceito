import { Link, useNavigate } from "react-router-dom";
import { ShoppingCartIcon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/contexts/CartContext";
import { Button } from "@/components/ui/button";

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { totalItens } = useCart();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <header className="flex items-center justify-between border-b border-border px-4 py-3">
      <Link to="/" className="font-semibold">
        Royal Conceito
      </Link>

      <nav className="flex items-center gap-3 text-sm">
        <Link to="/meus-pedidos" className="text-muted-foreground hover:text-foreground">
          Meus Pedidos
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

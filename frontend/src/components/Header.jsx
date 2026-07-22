import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
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

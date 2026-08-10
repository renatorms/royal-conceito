import { Link } from "react-router-dom";

// Social links are placeholders (href="#") — Royal Conceito's real social
// handles aren't defined yet. Swap for real URLs once they exist; see
// CLAUDE.md.
export function Footer() {
  const ano = new Date().getFullYear();

  return (
    <footer className="border-t border-border px-4 py-8 text-sm text-muted-foreground">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 md:flex-row md:justify-between">
        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <Link to="/sobre" className="hover:text-foreground">
            Quem Somos
          </Link>
          <Link to="/privacidade" className="hover:text-foreground">
            Política de Privacidade
          </Link>
          <a href="#" className="hover:text-foreground">
            Instagram
          </a>
          <a href="#" className="hover:text-foreground">
            WhatsApp
          </a>
        </nav>

        <p className="text-xs">© {ano} Royal Conceito. Todos os direitos reservados.</p>
      </div>
    </footer>
  );
}

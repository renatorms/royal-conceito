import { Link, useNavigate } from "react-router-dom";
import {
  ChevronRightIcon,
  HeartIcon,
  LogOutIcon,
  MapPinIcon,
  PackageIcon,
  RefreshCcwIcon,
  UserIcon,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

// Replaces Perfil.jsx entirely, 10/08 — that page mixed an account-info
// form and a "pedidos recentes" preview in one screen; this is a pure
// navigation hub instead (5 rows: 4 destinations + one action), with the
// account-info form moved to its own page (MinhaContaDados.jsx). The
// "pedidos recentes" preview wasn't carried over — "Meus Pedidos" below is
// one click away, and a hub whose job is *getting you somewhere* doesn't
// need to also render live order data itself; see CLAUDE.md.
const ITENS_NAVEGACAO = [
  {
    to: "/meus-pedidos",
    icone: PackageIcon,
    titulo: "Meus Pedidos",
    descricao: "Acompanhe seus pedidos e veja o histórico de compras.",
  },
  {
    to: "/minha-conta/dados",
    icone: UserIcon,
    titulo: "Informações da Conta",
    descricao: "E-mail, telefone e senha.",
  },
  {
    to: "/meus-enderecos",
    icone: MapPinIcon,
    titulo: "Meus Endereços",
    descricao: "Gerencie os endereços salvos para entrega.",
  },
  {
    to: "/meus-favoritos",
    icone: HeartIcon,
    titulo: "Meus Favoritos",
    descricao: "Veja os produtos que você salvou como favoritos.",
  },
  {
    to: "/trocas-e-devolucoes",
    icone: RefreshCcwIcon,
    titulo: "Trocas e Devoluções",
    descricao: "Solicite ou acompanhe uma troca/devolução.",
  },
];

export default function MinhaConta() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Minha Conta</h1>

      <div className="flex flex-col gap-3">
        {ITENS_NAVEGACAO.map(({ to, icone: Icone, titulo, descricao }) => (
          <Link
            key={to}
            to={to}
            className="flex items-center gap-4 rounded-lg border border-border p-4 hover:border-primary/50"
          >
            <Icone className="size-5 shrink-0 text-primary" />
            <div className="flex-1">
              <p className="font-medium">{titulo}</p>
              <p className="text-sm text-muted-foreground">{descricao}</p>
            </div>
            <ChevronRightIcon className="size-4 shrink-0 text-muted-foreground" />
          </Link>
        ))}

        {/* Não é um Link — "Sair" é uma ação (chama logout() direto), não
            uma navegação para outra página, então fica fora do map()
            acima em vez de forçar esse item numa lista pensada para
            destinos. */}
        <button
          type="button"
          onClick={handleLogout}
          className="flex items-center gap-4 rounded-lg border border-border p-4 text-left hover:border-destructive/50"
        >
          <LogOutIcon className="size-5 shrink-0 text-destructive" />
          <div className="flex-1">
            <p className="font-medium text-destructive">Sair</p>
            <p className="text-sm text-muted-foreground">Encerrar sua sessão.</p>
          </div>
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/contexts/AuthContext";
import { listarPedidos } from "@/api/pedidos";
import { perfilSchema } from "@/schemas/perfilSchema";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PedidoStatusBadge } from "@/components/PedidoStatusBadge";
import { formatarPreco } from "@/lib/utils";

// Only the most recent orders — this page isn't a replacement for
// /meus-pedidos (which has real pagination), just a quick-glance summary
// with a link into the full list.
const TOTAL_PEDIDOS_RESUMO = 5;

function formatarData(dataIso) {
  return new Intl.DateTimeFormat("pt-BR").format(new Date(dataIso));
}

export default function Perfil() {
  const { user, atualizarPerfil } = useAuth();
  const [sucesso, setSucesso] = useState(false);
  const [generalError, setGeneralError] = useState(null);

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(perfilSchema),
    defaultValues: { email: user.email },
  });

  async function onSubmit(values) {
    setSucesso(false);
    setGeneralError(null);
    const result = await atualizarPerfil(values);

    if (result.success) {
      setSucesso(true);
      reset(values);
      return;
    }

    applyApiErrors(result.error, setError, setGeneralError);
  }

  const [pedidos, setPedidos] = useState({ itens: [], carregando: true, erro: null });

  useEffect(() => {
    let ignore = false;

    listarPedidos({ page: 1 })
      .then((data) => {
        if (ignore) return;
        // Pedido has no default ordering on the backend (see CLAUDE.md) —
        // sorted here rather than trusted from the API, so "mais recentes"
        // is guaranteed regardless of whatever order the server happens to
        // return today.
        const maisRecentes = [...data.results]
          .sort((a, b) => new Date(b.data_pedido) - new Date(a.data_pedido))
          .slice(0, TOTAL_PEDIDOS_RESUMO);
        setPedidos({ itens: maisRecentes, carregando: false, erro: null });
      })
      .catch(() => {
        if (ignore) return;
        setPedidos({ itens: [], carregando: false, erro: "Não foi possível carregar seus pedidos." });
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Meu Perfil</h1>

      <section className="mb-10 rounded-xl border border-border p-6">
        <h2 className="mb-4 text-lg font-medium">Dados da conta</h2>

        {generalError && (
          <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {generalError}
          </p>
        )}
        {sucesso && (
          <p className="mb-4 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
            Dados atualizados com sucesso.
          </p>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="username">Usuário</Label>
            <Input id="username" value={user.username} disabled readOnly />
            <p className="text-xs text-muted-foreground">
              O nome de usuário não pode ser alterado.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email">E-mail</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register("email", {
                onChange: () => setSucesso(false),
              })}
            />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Salvando..." : "Salvar alterações"}
          </Button>
        </form>
      </section>

      <section className="rounded-xl border border-border p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-medium">Pedidos recentes</h2>
          <Link
            to="/meus-pedidos"
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            Ver todos os pedidos
          </Link>
        </div>

        {pedidos.erro ? (
          <p className="text-sm text-destructive">{pedidos.erro}</p>
        ) : pedidos.carregando ? (
          <p className="text-sm text-muted-foreground">Carregando pedidos...</p>
        ) : pedidos.itens.length === 0 ? (
          <p className="text-sm text-muted-foreground">Você ainda não fez nenhum pedido.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {pedidos.itens.map((pedido) => (
              <Link
                key={pedido.id}
                to={`/meus-pedidos/${pedido.id}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3 hover:border-primary/50"
              >
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium">Pedido #{pedido.id}</span>
                  <span className="text-xs text-muted-foreground">
                    {formatarData(pedido.data_pedido)}
                  </span>
                </div>
                <PedidoStatusBadge status={pedido.status} />
                <span className="text-sm font-semibold">{formatarPreco(pedido.total)}</span>
              </Link>
            ))}
          </div>
        )}

        <Link
          to="/meus-enderecos"
          className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
        >
          Gerenciar meus endereços
        </Link>
      </section>
    </div>
  );
}

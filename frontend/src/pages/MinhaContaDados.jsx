import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeftIcon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { dadosContaSchema } from "@/schemas/dadosContaSchema";
import { senhaSchema } from "@/schemas/senhaSchema";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Two independent forms, two independent useForm() instances/submissions —
// same reasoning as Perfil.jsx's old "Dados da conta"/"Pedidos recentes"
// split (one section failing/succeeding shouldn't affect the other), just
// applied to two *forms* instead of a form + a data list. Reused from
// Perfil.jsx: the email field, its validation pattern, and the
// success-banner-cleared-on-edit behavior; extended with `telefone` (also
// from AtualizarPerfilSerializer, see CLAUDE.md).
function DadosDaConta() {
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
    resolver: zodResolver(dadosContaSchema),
    defaultValues: { email: user.email, telefone: user.telefone || "" },
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

  return (
    <section className="rounded-xl border border-border p-6">
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
          <p className="text-xs text-muted-foreground">O nome de usuário não pode ser alterado.</p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            aria-invalid={!!errors.email}
            {...register("email", { onChange: () => setSucesso(false) })}
          />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="telefone">Telefone</Label>
          <Input
            id="telefone"
            type="tel"
            autoComplete="tel"
            placeholder="(11) 91234-5678"
            aria-invalid={!!errors.telefone}
            {...register("telefone", { onChange: () => setSucesso(false) })}
          />
          {errors.telefone && (
            <p className="text-sm text-destructive">{errors.telefone.message}</p>
          )}
        </div>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : "Salvar alterações"}
        </Button>
      </form>
    </section>
  );
}

function AlterarSenha() {
  const { alterarSenha } = useAuth();
  const [sucesso, setSucesso] = useState(false);
  const [generalError, setGeneralError] = useState(null);

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(senhaSchema),
    defaultValues: { senha_atual: "", nova_senha: "", confirmar_nova_senha: "" },
  });

  async function onSubmit(values) {
    setSucesso(false);
    setGeneralError(null);
    // `confirmar_nova_senha` é validação só do frontend (ver senhaSchema.js)
    // — o backend não conhece esse campo, só senha_atual/nova_senha.
    const { senha_atual, nova_senha } = values;
    const result = await alterarSenha({ senha_atual, nova_senha });

    if (result.success) {
      setSucesso(true);
      reset({ senha_atual: "", nova_senha: "", confirmar_nova_senha: "" });
      return;
    }

    applyApiErrors(result.error, setError, setGeneralError);
  }

  return (
    <section className="rounded-xl border border-border p-6">
      <h2 className="mb-4 text-lg font-medium">Alterar senha</h2>

      {generalError && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {generalError}
        </p>
      )}
      {sucesso && (
        <p className="mb-4 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
          Senha alterada com sucesso.
        </p>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="senha_atual">Senha atual</Label>
          <Input
            id="senha_atual"
            type="password"
            autoComplete="current-password"
            aria-invalid={!!errors.senha_atual}
            {...register("senha_atual", { onChange: () => setSucesso(false) })}
          />
          {errors.senha_atual && (
            <p className="text-sm text-destructive">{errors.senha_atual.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="nova_senha">Nova senha</Label>
          <Input
            id="nova_senha"
            type="password"
            autoComplete="new-password"
            aria-invalid={!!errors.nova_senha}
            {...register("nova_senha", { onChange: () => setSucesso(false) })}
          />
          {errors.nova_senha && (
            <p className="text-sm text-destructive">{errors.nova_senha.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmar_nova_senha">Confirmar nova senha</Label>
          <Input
            id="confirmar_nova_senha"
            type="password"
            autoComplete="new-password"
            aria-invalid={!!errors.confirmar_nova_senha}
            {...register("confirmar_nova_senha", { onChange: () => setSucesso(false) })}
          />
          {errors.confirmar_nova_senha && (
            <p className="text-sm text-destructive">{errors.confirmar_nova_senha.message}</p>
          )}
        </div>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : "Alterar senha"}
        </Button>
      </form>
    </section>
  );
}

export default function MinhaContaDados() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Link
        to="/minha-conta"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeftIcon className="size-4" />
        Minha Conta
      </Link>

      <h1 className="mb-6 text-2xl font-semibold">Informações da Conta</h1>

      <div className="flex flex-col gap-6">
        <DadosDaConta />
        <AlterarSenha />
      </div>
    </div>
  );
}

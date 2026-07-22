import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { loginSchema } from "@/schemas/loginSchema";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [generalError, setGeneralError] = useState(null);
  const successMessage = location.state?.message;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: location.state?.username ?? "",
      password: "",
    },
  });

  async function onSubmit(values) {
    setGeneralError(null);
    const result = await login(values.username, values.password);

    if (result.success) {
      const from = location.state?.from?.pathname ?? "/";
      navigate(from, { replace: true });
      return;
    }

    applyApiErrors(result.error, setError, setGeneralError);
  }

  return (
    <div className="mx-auto flex w-full max-w-sm flex-col justify-center gap-6 px-4 py-16">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold">Entrar</h1>
        <p className="text-sm text-muted-foreground">
          Acesse sua conta Royal Conceito.
        </p>
      </div>

      {successMessage && (
        <p className="rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
          {successMessage}
        </p>
      )}
      {generalError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {generalError}
        </p>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="username">Usuário</Label>
          <Input
            id="username"
            autoComplete="username"
            aria-invalid={!!errors.username}
            {...register("username")}
          />
          {errors.username && (
            <p className="text-sm text-destructive">{errors.username.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Senha</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={!!errors.password}
            {...register("password")}
          />
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Entrando..." : "Entrar"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Não tem conta?{" "}
        <Link to="/registro" className="text-primary underline-offset-4 hover:underline">
          Cadastre-se
        </Link>
      </p>
    </div>
  );
}

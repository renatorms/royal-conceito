import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { registroSchema } from "@/schemas/registroSchema";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Registro() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [generalError, setGeneralError] = useState(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registroSchema),
    defaultValues: {
      username: "",
      email: "",
      password: "",
      confirmarSenha: "",
    },
  });

  async function onSubmit(values) {
    setGeneralError(null);
    const result = await registerUser({
      username: values.username,
      email: values.email,
      password: values.password,
    });

    if (result.success) {
      navigate("/login", {
        replace: true,
        state: {
          message: "Cadastro realizado com sucesso! Faça login para continuar.",
          username: values.username,
        },
      });
      return;
    }

    applyApiErrors(result.error, setError, setGeneralError);
  }

  return (
    <div className="mx-auto flex w-full max-w-sm flex-col justify-center gap-6 px-4 py-16">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold">Criar conta</h1>
        <p className="text-sm text-muted-foreground">
          Cadastre-se para comprar na Royal Conceito.
        </p>
      </div>

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
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Senha</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            aria-invalid={!!errors.password}
            {...register("password")}
          />
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmarSenha">Confirmar senha</Label>
          <Input
            id="confirmarSenha"
            type="password"
            autoComplete="new-password"
            aria-invalid={!!errors.confirmarSenha}
            {...register("confirmarSenha")}
          />
          {errors.confirmarSenha && (
            <p className="text-sm text-destructive">{errors.confirmarSenha.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Cadastrando..." : "Cadastrar"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Já tem conta?{" "}
        <Link to="/login" className="text-primary underline-offset-4 hover:underline">
          Entrar
        </Link>
      </p>
    </div>
  );
}

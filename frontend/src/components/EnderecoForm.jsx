import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { enderecoSchema } from "@/schemas/enderecoSchema";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const VALORES_VAZIOS = {
  rua: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  estado: "",
  cep: "",
};

// Formulário de endereço reutilizado por MeusEnderecos.jsx para criar e
// editar. Diferente do endereço em Checkout.jsx (que dispara `trigger()`
// manualmente porque é só uma parte opcional de uma ação maior), aqui o
// formulário É a ação inteira, então usa `handleSubmit()` normalmente — o
// mesmo padrão de Login.jsx/Registro.jsx.
export function EnderecoForm({ defaultValues, onSalvar, onCancelar, submitLabel = "Salvar" }) {
  const [enviando, setEnviando] = useState(false);
  const [erroGeral, setErroGeral] = useState(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(enderecoSchema),
    defaultValues: defaultValues ?? VALORES_VAZIOS,
  });

  async function onSubmit(dados) {
    setErroGeral(null);
    setEnviando(true);
    try {
      await onSalvar(dados);
    } catch (error) {
      applyApiErrors(error.response?.data, setError, setErroGeral);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      {erroGeral && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {erroGeral}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="rua">Rua</Label>
          <Input id="rua" aria-invalid={!!errors.rua} {...register("rua")} />
          {errors.rua && <p className="text-sm text-destructive">{errors.rua.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="numero">Número</Label>
          <Input
            id="numero"
            inputMode="numeric"
            aria-invalid={!!errors.numero}
            {...register("numero")}
          />
          {errors.numero && <p className="text-sm text-destructive">{errors.numero.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="complemento">Complemento</Label>
          <Input id="complemento" {...register("complemento")} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="bairro">Bairro</Label>
          <Input id="bairro" aria-invalid={!!errors.bairro} {...register("bairro")} />
          {errors.bairro && <p className="text-sm text-destructive">{errors.bairro.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="cidade">Cidade</Label>
          <Input id="cidade" aria-invalid={!!errors.cidade} {...register("cidade")} />
          {errors.cidade && <p className="text-sm text-destructive">{errors.cidade.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="estado">Estado (UF)</Label>
          <Input
            id="estado"
            maxLength={2}
            aria-invalid={!!errors.estado}
            {...register("estado")}
          />
          {errors.estado && <p className="text-sm text-destructive">{errors.estado.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="cep">CEP</Label>
          <Input id="cep" aria-invalid={!!errors.cep} {...register("cep")} />
          {errors.cep && <p className="text-sm text-destructive">{errors.cep.message}</p>}
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={enviando}>
          {enviando ? "Salvando..." : submitLabel}
        </Button>
        {onCancelar && (
          <Button type="button" variant="outline" disabled={enviando} onClick={onCancelar}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  );
}

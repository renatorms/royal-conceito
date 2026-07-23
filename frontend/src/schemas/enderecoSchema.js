import { z } from "zod";

export const enderecoSchema = z.object({
  rua: z.string().min(1, "Informe a rua.").max(100, "Máximo de 100 caracteres."),
  numero: z.coerce
    .number({ invalid_type_error: "Informe um número válido." })
    .int("Informe um número válido.")
    .positive("Informe um número válido."),
  complemento: z.string().max(100, "Máximo de 100 caracteres.").optional(),
  bairro: z.string().min(1, "Informe o bairro.").max(100, "Máximo de 100 caracteres."),
  cidade: z.string().min(1, "Informe a cidade.").max(100, "Máximo de 100 caracteres."),
  estado: z
    .string()
    .length(2, "Use a sigla do estado (UF), ex: SP.")
    .transform((valor) => valor.toUpperCase()),
  cep: z.string().regex(/^\d{5}-?\d{3}$/, "CEP inválido. Use o formato 00000-000."),
});

import { z } from "zod";

export const registroSchema = z
  .object({
    username: z.string().min(1, "Informe um nome de usuário."),
    email: z.string().min(1, "Informe seu e-mail.").email("E-mail inválido."),
    password: z.string().min(8, "A senha deve ter pelo menos 8 caracteres."),
    confirmarSenha: z.string().min(1, "Confirme sua senha."),
  })
  .refine((data) => data.password === data.confirmarSenha, {
    message: "As senhas não coincidem.",
    path: ["confirmarSenha"],
  });

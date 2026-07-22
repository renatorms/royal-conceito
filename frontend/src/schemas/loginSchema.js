import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(1, "Informe seu usuário."),
  password: z.string().min(1, "Informe sua senha."),
});

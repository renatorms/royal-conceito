import { z } from "zod";

// Only `email` — `username` isn't editable through this form at all (see
// AtualizarPerfilSerializer/usuarios/serializers.py for the backend
// reasoning: it's the login identifier, not an ordinary profile field).
export const perfilSchema = z.object({
  email: z.string().min(1, "Informe seu e-mail.").email("E-mail inválido."),
});

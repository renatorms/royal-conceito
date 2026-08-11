import { z } from "zod";

// Renamed from perfilSchema.js 10/08, alongside Perfil.jsx becoming
// MinhaConta.jsx (a hub) + MinhaContaDados.jsx (this form's new home) — see
// CLAUDE.md. Only `email`/`telefone` — `username` isn't editable through
// this form at all (see AtualizarPerfilSerializer/usuarios/serializers.py
// for the backend reasoning: it's the login identifier, not an ordinary
// profile field). `telefone` is optional and deliberately unformatted (no
// regex/mask): the backend stores it as free text too (see
// PerfilUsuario.telefone), so there's nothing here to keep in sync with a
// stricter backend rule.
export const dadosContaSchema = z.object({
  email: z.string().min(1, "Informe seu e-mail.").email("E-mail inválido."),
  telefone: z.string().max(20, "Máximo de 20 caracteres.").optional().or(z.literal("")),
});

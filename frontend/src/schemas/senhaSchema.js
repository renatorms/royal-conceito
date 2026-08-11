import { z } from "zod";

// Mirrors registroSchema.js's password-confirmation shape (.refine() on the
// object, not a per-field check) — `senha_atual` deliberately has no
// min-length rule of its own here: whatever the real rule was when this
// account's password was originally set is the backend's problem to check
// (POST /api/me/senha/ calls check_password()), not something to
// re-validate client-side. `nova_senha`'s min(8) is just a fast client-side
// signal — the real, authoritative rule is Django's own validate_password()
// (AUTH_PASSWORD_VALIDATORS, core/settings.py), enforced server-side and
// surfaced via applyApiErrors() if this quick check somehow passes but the
// backend's fuller rule set (common-password/similarity/numeric-only
// checks) doesn't.
export const senhaSchema = z
  .object({
    senha_atual: z.string().min(1, "Informe sua senha atual."),
    nova_senha: z.string().min(8, "A nova senha deve ter pelo menos 8 caracteres."),
    confirmar_nova_senha: z.string().min(1, "Confirme sua nova senha."),
  })
  .refine((data) => data.nova_senha === data.confirmar_nova_senha, {
    message: "As senhas não coincidem.",
    path: ["confirmar_nova_senha"],
  });

import { cn } from "@/lib/utils";

const STATUS_LABELS = {
  novo: "Novo",
  confirmado: "Confirmado",
  enviado: "Enviado",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

// Dark-theme pill colors — fixed 2026-08-11 (was a hardcoded light-mode
// palette, bg-*-100/text-*-700, that read as a bright pastel box against
// the near-black brand background; see CLAUDE.md). Semi-transparent
// -500/15 fills read as a tinted dark chip rather than a solid block, and
// -300 text keeps contrast comfortable on that near-black background.
// "cancelado" reuses the theme's own --destructive token (already a
// dark-mode-tuned red) instead of a raw Tailwind red, per the project's
// existing bg-destructive/10 text-destructive convention (see
// Login.jsx/EnderecoForm.jsx) — every other status keeps a distinct
// Tailwind hue since the theme defines no blue/amber/purple/green tokens.
const STATUS_CLASSES = {
  novo: "bg-blue-500/15 text-blue-300",
  confirmado: "bg-amber-500/15 text-amber-300",
  enviado: "bg-purple-500/15 text-purple-300",
  entregue: "bg-green-500/15 text-green-300",
  cancelado: "bg-destructive/15 text-destructive",
};

export function PedidoStatusBadge({ status, className }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_CLASSES[status] ?? "bg-muted text-muted-foreground",
        className
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

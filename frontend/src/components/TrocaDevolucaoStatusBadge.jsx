import { cn } from "@/lib/utils";

// Adapted from PedidoStatusBadge.jsx — same shape (label/color lookup +
// muted fallback for an unrecognized value), different status set
// (SolicitacaoTrocaDevolucao.STATUS_CHOICES, not Pedido.STATUS_CHOICES).
// Kept as its own component rather than generalizing PedidoStatusBadge to
// take a lookup table as a prop: the two status sets are unrelated
// (different model, different meaning), and there are only two call sites
// total between them — not enough duplication yet to justify the extra
// indirection of a shared, table-driven component.
const STATUS_LABELS = {
  pendente: "Pendente",
  em_analise: "Em análise",
  aprovada: "Aprovada",
  rejeitada: "Rejeitada",
  concluida: "Concluída",
};

// Dark-theme pill colors — same fix, and same reasoning, as
// PedidoStatusBadge.jsx (see the comment there): -500/15 fills + -300 text
// for the three hues the theme has no token for, bg-destructive/15
// text-destructive (the project's existing convention) for the one status
// that's semantically an error/negative outcome.
const STATUS_CLASSES = {
  pendente: "bg-blue-500/15 text-blue-300",
  em_analise: "bg-amber-500/15 text-amber-300",
  aprovada: "bg-green-500/15 text-green-300",
  rejeitada: "bg-destructive/15 text-destructive",
  concluida: "bg-purple-500/15 text-purple-300",
};

export function TrocaDevolucaoStatusBadge({ status, className }) {
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

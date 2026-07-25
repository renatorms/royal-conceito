import { cn } from "@/lib/utils";

const STATUS_LABELS = {
  novo: "Novo",
  confirmado: "Confirmado",
  enviado: "Enviado",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

const STATUS_CLASSES = {
  novo: "bg-blue-100 text-blue-700",
  confirmado: "bg-amber-100 text-amber-700",
  enviado: "bg-purple-100 text-purple-700",
  entregue: "bg-green-100 text-green-700",
  cancelado: "bg-red-100 text-red-700",
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

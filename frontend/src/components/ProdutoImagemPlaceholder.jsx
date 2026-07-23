import { ShirtIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProdutoImagemPlaceholder({ className }) {
  return (
    <div
      className={cn(
        "flex aspect-square items-center justify-center bg-muted text-muted-foreground",
        className
      )}
    >
      <ShirtIcon className="size-10" strokeWidth={1.5} />
    </div>
  );
}

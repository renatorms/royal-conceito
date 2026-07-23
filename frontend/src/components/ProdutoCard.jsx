import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { formatarPreco } from "@/lib/utils";

export function ProdutoCard({ produto }) {
  return (
    <Link to={`/produtos/${produto.id}`} className="block">
      <Card className="p-0 transition-shadow hover:shadow-md">
        <ProdutoImagemPlaceholder />
        <CardContent className="flex flex-col gap-1 px-4 py-3">
          {produto.marca_nome && (
            <span className="text-xs text-muted-foreground">{produto.marca_nome}</span>
          )}
          <span className="line-clamp-2 text-sm font-medium">{produto.nome}</span>
          <span className="text-sm font-semibold">{formatarPreco(produto.preco)}</span>
        </CardContent>
      </Card>
    </Link>
  );
}

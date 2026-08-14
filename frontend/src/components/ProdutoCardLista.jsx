import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { formatarPreco } from "@/lib/utils";

// Contraparte de ProdutoCard.jsx para o modo de visualização "lista" do
// Catálogo (Catalogo.jsx) — mesma linha horizontal compacta usada por
// qualquer e-commerce em modo lista: imagem pequena à esquerda, nome/marca/
// preço à direita. Reaproveita os mesmos dados de `produto` já carregados
// pelo grid, nenhuma chamada de API própria.
export function ProdutoCardLista({ produto }) {
  const imagemSrc = produto.imagem || produto.imagem_url;

  return (
    <Link to={`/produtos/${produto.id}`} className="block">
      <Card className="flex flex-row items-center gap-4 p-3 transition-shadow hover:shadow-md">
        <div className="size-16 shrink-0 overflow-hidden rounded-md">
          {imagemSrc ? (
            <img
              src={imagemSrc}
              alt={produto.nome}
              className="size-16 object-cover"
            />
          ) : (
            <ProdutoImagemPlaceholder className="size-16" />
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          {produto.marca_nome && (
            <span className="text-xs text-muted-foreground">{produto.marca_nome}</span>
          )}
          <span className="truncate text-sm font-medium">{produto.nome}</span>
        </div>
        <span className="shrink-0 text-sm font-semibold">{formatarPreco(produto.preco)}</span>
      </Card>
    </Link>
  );
}

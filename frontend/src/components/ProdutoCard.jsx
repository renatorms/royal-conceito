import { Link } from "react-router-dom";
import { HeartIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { ProdutoImagemPlaceholder } from "@/components/ProdutoImagemPlaceholder";
import { cn, formatarPreco } from "@/lib/utils";

// isFavorito/onToggleFavorito/favoritoSalvando são opcionais — quando
// onToggleFavorito não é passado (ex: grid "Mais produtos" de
// ProdutoDetalhe.jsx, cards de MeusFavoritos.jsx que já tem seu próprio
// botão de remover), nenhum coração é renderizado, mantendo este
// componente compatível com todo chamador existente.
export function ProdutoCard({ produto, isFavorito, onToggleFavorito, favoritoSalvando }) {
  const imagemSrc = produto.imagem || produto.imagem_url;

  return (
    <div className="relative">
      <Link to={`/produtos/${produto.id}`} className="block">
        <Card className="p-0 transition-shadow hover:shadow-md">
          {imagemSrc ? (
            <img
              src={imagemSrc}
              alt={produto.nome}
              className="aspect-square w-full object-cover"
            />
          ) : (
            <ProdutoImagemPlaceholder />
          )}
          <CardContent className="flex flex-col gap-1 px-4 py-3">
            {produto.marca_nome && (
              <span className="text-xs text-muted-foreground">{produto.marca_nome}</span>
            )}
            <span className="line-clamp-2 text-sm font-medium">{produto.nome}</span>
            <span className="text-sm font-semibold text-primary">
              {formatarPreco(produto.preco)}
            </span>
          </CardContent>
        </Card>
      </Link>

      {/* Irmão do Link, não filho dele — mesmo cuidado já usado em
          MeusFavoritos.jsx pra clicar no coração sem navegar pro
          produto (sem precisar de stopPropagation/preventDefault). */}
      {onToggleFavorito && (
        <button
          type="button"
          aria-label={isFavorito ? "Remover dos favoritos" : "Adicionar aos favoritos"}
          aria-pressed={isFavorito}
          disabled={favoritoSalvando}
          onClick={onToggleFavorito}
          className="absolute right-2 top-2 z-10 flex size-8 items-center justify-center rounded-full bg-background/90 shadow hover:text-destructive disabled:opacity-50"
        >
          <HeartIcon className={cn("size-4", isFavorito && "fill-destructive text-destructive")} />
        </button>
      )}
    </div>
  );
}

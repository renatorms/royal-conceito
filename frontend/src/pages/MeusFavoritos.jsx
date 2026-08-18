import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { XIcon } from "lucide-react";
import { deletarFavorito, listarFavoritos } from "@/api/favoritos";
import { ProdutoCard } from "@/components/ProdutoCard";

export default function MeusFavoritos() {
  const [resultado, setResultado] = useState({ carregado: false, favoritos: [], erro: null });

  useEffect(() => {
    let ignore = false;

    listarFavoritos()
      .then((favoritos) => {
        if (!ignore) setResultado({ carregado: true, favoritos, erro: null });
      })
      .catch(() => {
        if (!ignore) {
          setResultado({
            carregado: true,
            favoritos: [],
            erro: "Não foi possível carregar seus favoritos.",
          });
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  async function handleRemover(favoritoId) {
    setResultado((atual) => ({
      ...atual,
      favoritos: atual.favoritos.filter((f) => f.id !== favoritoId),
    }));
    try {
      await deletarFavorito(favoritoId);
    } catch {
      // Falha na remoção: recarrega a lista real do backend em vez de
      // deixar o card removido otimisticamente desaparecer por engano.
      listarFavoritos().then((favoritos) => setResultado({ carregado: true, favoritos, erro: null }));
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Meus Favoritos</h1>

      {resultado.erro ? (
        <p className="text-sm text-destructive">{resultado.erro}</p>
      ) : !resultado.carregado ? (
        <p className="text-sm text-muted-foreground">Carregando favoritos...</p>
      ) : resultado.favoritos.length === 0 ? (
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Você ainda não adicionou nenhum produto aos favoritos.
          </p>
          <Link
            to="/"
            className="mt-4 inline-block text-sm text-primary underline-offset-4 hover:underline"
          >
            Ver catálogo
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {resultado.favoritos.map((favorito) => (
            <div key={favorito.id} className="relative">
              <ProdutoCard produto={favorito.produto} />
              <button
                type="button"
                aria-label="Remover dos favoritos"
                onClick={() => handleRemover(favorito.id)}
                className="absolute right-2 top-2 z-10 flex size-8 items-center justify-center rounded-full bg-background/90 text-foreground shadow hover:text-destructive"
              >
                <XIcon className="size-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

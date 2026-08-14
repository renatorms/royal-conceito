import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-3 px-4 py-24 text-center">
      <h1 className="text-2xl font-semibold">Página não encontrada</h1>
      <p className="text-sm text-muted-foreground">
        O endereço acessado não existe ou foi movido.
      </p>
      <Link
        to="/"
        className="mt-2 text-sm text-primary underline-offset-4 hover:underline"
      >
        Voltar ao catálogo
      </Link>
    </div>
  );
}

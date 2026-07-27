import { useEffect, useState } from "react";
import { PencilIcon, PlusIcon, Trash2Icon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { listarEnderecos, criarEndereco, atualizarEndereco, deletarEndereco } from "@/api/enderecos";
import { EnderecoForm } from "@/components/EnderecoForm";
import { Button } from "@/components/ui/button";

const NOVO = "novo";

export default function MeusEnderecos() {
  const { user } = useAuth();

  const [enderecos, setEnderecos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [erro, setErro] = useState(null);
  const [erroExcluir, setErroExcluir] = useState(null);
  // id do endereço em edição, NOVO (formulário de cadastro aberto), ou null
  const [modoEdicao, setModoEdicao] = useState(null);

  useEffect(() => {
    let ignore = false;

    listarEnderecos()
      .then((data) => {
        if (ignore) return;
        setEnderecos(data);
        setErro(null);
      })
      .catch(() => {
        if (ignore) return;
        setErro("Não foi possível carregar seus endereços.");
      })
      .finally(() => {
        if (!ignore) setIsLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  async function handleCriar(dados) {
    // Endereco.usuario não tem blank=True no model, então o serializer exige
    // o campo mesmo com perform_create() sobrescrevendo-o com request.user
    // logo em seguida — só evita o 400 de validação (mesmo quirk do Checkout).
    const novo = await criarEndereco({ ...dados, usuario: user.id });
    setEnderecos((atual) => [...atual, novo]);
    setModoEdicao(null);
  }

  async function handleAtualizar(id, dados) {
    const atualizado = await atualizarEndereco(id, dados);
    setEnderecos((atual) => atual.map((endereco) => (endereco.id === id ? atualizado : endereco)));
    setModoEdicao(null);
  }

  async function handleExcluir(id) {
    if (!window.confirm("Tem certeza que deseja excluir este endereço?")) return;

    setErroExcluir(null);
    try {
      await deletarEndereco(id);
      setEnderecos((atual) => atual.filter((endereco) => endereco.id !== id));
    } catch (error) {
      setErroExcluir(
        error.response?.data?.detail || "Não foi possível excluir este endereço. Tente novamente."
      );
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Meus Endereços</h1>

      {erroExcluir && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {erroExcluir}
        </p>
      )}

      {erro ? (
        <p className="text-sm text-destructive">{erro}</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando endereços...</p>
      ) : (
        <div className="flex flex-col gap-3">
          {enderecos.length === 0 && modoEdicao !== NOVO && (
            <p className="text-sm text-muted-foreground">Nenhum endereço cadastrado ainda.</p>
          )}

          {enderecos.map((endereco) =>
            modoEdicao === endereco.id ? (
              <div key={endereco.id} className="rounded-xl border border-border p-4">
                <EnderecoForm
                  defaultValues={{
                    rua: endereco.rua,
                    numero: String(endereco.numero),
                    complemento: endereco.complemento ?? "",
                    bairro: endereco.bairro,
                    cidade: endereco.cidade,
                    estado: endereco.estado,
                    cep: endereco.cep,
                  }}
                  onSalvar={(dados) => handleAtualizar(endereco.id, dados)}
                  onCancelar={() => setModoEdicao(null)}
                  submitLabel="Salvar alterações"
                />
              </div>
            ) : (
              <div
                key={endereco.id}
                className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-border p-4"
              >
                <p className="text-sm">
                  {endereco.rua}, {endereco.numero}
                  {endereco.complemento ? ` - ${endereco.complemento}` : ""} — {endereco.bairro},{" "}
                  {endereco.cidade}/{endereco.estado} — CEP {endereco.cep}
                </p>
                <div className="flex shrink-0 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setModoEdicao(endereco.id)}
                  >
                    <PencilIcon /> Editar
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => handleExcluir(endereco.id)}
                  >
                    <Trash2Icon /> Excluir
                  </Button>
                </div>
              </div>
            )
          )}
        </div>
      )}

      {!isLoading &&
        !erro &&
        (modoEdicao === NOVO ? (
          <div className="mt-6 rounded-xl border border-border p-4">
            <h2 className="mb-3 text-lg font-medium">Novo endereço</h2>
            <EnderecoForm
              onSalvar={handleCriar}
              onCancelar={() => setModoEdicao(null)}
              submitLabel="Cadastrar endereço"
            />
          </div>
        ) : (
          <Button type="button" variant="outline" className="mt-6" onClick={() => setModoEdicao(NOVO)}>
            <PlusIcon /> Adicionar novo endereço
          </Button>
        ))}
    </div>
  );
}

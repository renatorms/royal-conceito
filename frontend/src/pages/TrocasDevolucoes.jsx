import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronLeftIcon } from "lucide-react";
import { listarPedidos } from "@/api/pedidos";
import { criarSolicitacao, listarSolicitacoes } from "@/api/trocasDevolucoes";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TrocaDevolucaoStatusBadge } from "@/components/TrocaDevolucaoStatusBadge";
import { formatarPreco } from "@/lib/utils";

const TIPO_ITEMS = [
  { value: "troca", label: "Troca" },
  { value: "devolucao", label: "Devolução" },
];

function formatarData(dataIso) {
  return new Intl.DateTimeFormat("pt-BR").format(new Date(dataIso));
}

// Mesmo formato "erro geral" que applyApiErrors() (src/lib/apiErrors.js)
// usaria para um payload {"detail": "..."} — não reaproveitado diretamente
// aqui porque esse helper foi desenhado em volta de um formulário
// react-hook-form (setError por campo + setGeneralError). O formulário
// desta página não usa react-hook-form (ver NovaSolicitacao abaixo): os
// campos são selects em cascata com estado próprio, não uma validação
// zod estática, então uma versão simples e independente é mais direta do
// que forçar esse formulário a se encaixar num helper pensado pra outro
// formato.
function extrairMensagemErro(errorData) {
  if (!errorData || typeof errorData !== "object") {
    return "Ocorreu um erro inesperado. Tente novamente.";
  }
  if (errorData.detail) return errorData.detail;
  const primeiraMensagem = Object.values(errorData).find(
    (msgs) => Array.isArray(msgs) && msgs.length > 0
  );
  return primeiraMensagem ? primeiraMensagem[0] : "Ocorreu um erro inesperado. Tente novamente.";
}

function NovaSolicitacao({ onCriada }) {
  const [pedidos, setPedidos] = useState({ itens: [], carregando: true, erro: null });
  const [pedidoId, setPedidoId] = useState("");
  const [itemId, setItemId] = useState("");
  const [tipo, setTipo] = useState("");
  const [motivo, setMotivo] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let ignore = false;

    // page: 1 apenas — mesma limitação documentada em CLAUDE.md para
    // qualquer tela que precise "escolher um Pedido já feito" sem ser a
    // própria lista paginada de Meus Pedidos: pedidos entregues fora da
    // página mais recente não aparecem aqui pra seleção. Não busca todas
    // as páginas (como listarEnderecos()) de propósito — Pedido.total é
    // ilimitado por natureza, carregar tudo de uma vez pra popular um
    // <select> reintroduziria exatamente o "carregar tudo adiantado" que
    // listarPedidos() foi desenhado pra evitar (ver CLAUDE.md).
    listarPedidos({ page: 1 })
      .then((data) => {
        if (ignore) return;
        const entregues = data.results.filter((p) => p.status === "entregue");
        setPedidos({ itens: entregues, carregando: false, erro: null });
      })
      .catch(() => {
        if (ignore) return;
        setPedidos({ itens: [], carregando: false, erro: "Não foi possível carregar seus pedidos." });
      });

    return () => {
      ignore = true;
    };
  }, []);

  const pedidoSelecionado = pedidos.itens.find((p) => String(p.id) === pedidoId) || null;
  // Os `itens` de cada Pedido já vêm aninhados na resposta de
  // listarPedidos() (PedidoSerializer.itens) — não é preciso um segundo
  // round-trip via buscarPedido() só para popular este select; buscarPedido()
  // segue existindo/sendo usado em PedidoDetalhe.jsx para a tela de detalhe
  // de um pedido específico, não é necessário aqui de novo.
  const itensDoPedido = pedidoSelecionado?.itens ?? [];

  function handlePedidoChange(valor) {
    setPedidoId(valor);
    setItemId("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErro(null);

    if (!pedidoId || !itemId || !tipo || !motivo.trim()) {
      setErro("Preencha todos os campos antes de enviar.");
      return;
    }

    setEnviando(true);
    try {
      await criarSolicitacao({ itemPedido: Number(itemId), tipo, motivo: motivo.trim() });
      setPedidoId("");
      setItemId("");
      setTipo("");
      setMotivo("");
      onCriada();
    } catch (error) {
      setErro(extrairMensagemErro(error.response?.data));
    } finally {
      setEnviando(false);
    }
  }

  if (pedidos.carregando) {
    return <p className="text-sm text-muted-foreground">Carregando seus pedidos...</p>;
  }

  if (pedidos.erro) {
    return <p className="text-sm text-destructive">{pedidos.erro}</p>;
  }

  if (pedidos.itens.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Você ainda não tem pedidos entregues — trocas e devoluções só podem ser solicitadas
        depois que o pedido chega.
      </p>
    );
  }

  const pedidoItems = pedidos.itens.map((p) => ({
    value: String(p.id),
    label: `Pedido #${p.id} - ${formatarData(p.data_pedido)} - ${formatarPreco(p.total)}`,
  }));
  const itemItems = itensDoPedido.map((item) => ({
    value: String(item.id),
    label: `${item.produto_nome} - Tam. ${item.produto_tamanho} (qtd: ${item.quantidade})`,
  }));

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {erro && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{erro}</p>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="pedido">Pedido</Label>
        <Select items={pedidoItems} value={pedidoId} onValueChange={handlePedidoChange}>
          <SelectTrigger id="pedido" className="w-full">
            <SelectValue placeholder="Selecione um pedido entregue" />
          </SelectTrigger>
          <SelectContent>
            {pedidoItems.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {pedidoSelecionado && (
        <div className="space-y-1.5">
          <Label htmlFor="item">Item</Label>
          <Select items={itemItems} value={itemId} onValueChange={setItemId}>
            <SelectTrigger id="item" className="w-full">
              <SelectValue placeholder="Selecione o item" />
            </SelectTrigger>
            <SelectContent>
              {itemItems.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="tipo">Tipo de solicitação</Label>
        <Select items={TIPO_ITEMS} value={tipo} onValueChange={setTipo}>
          <SelectTrigger id="tipo" className="w-full">
            <SelectValue placeholder="Troca ou devolução?" />
          </SelectTrigger>
          <SelectContent>
            {TIPO_ITEMS.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="motivo">Motivo</Label>
        <textarea
          id="motivo"
          rows={4}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          placeholder="Conte o que aconteceu..."
          className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
        />
      </div>

      <Button type="submit" disabled={enviando}>
        {enviando ? "Enviando..." : "Enviar solicitação"}
      </Button>
    </form>
  );
}

export default function TrocasDevolucoes() {
  const [solicitacoes, setSolicitacoes] = useState({ itens: [], carregando: true, erro: null });

  // Deliberadamente NÃO reseta `carregando: true` de forma síncrona logo no
  // início (o que violaria a regra de lint react-hooks/set-state-in-effect
  // quando chamada direto de dentro do useEffect abaixo — mesmo problema
  // documentado em CLAUDE.md para o padrão "chave" usado em
  // MeusPedidos.jsx/Catalogo.jsx). Consequência aceita: um refetch manual
  // (via onCriada, depois de abrir uma nova solicitação) atualiza a lista
  // silenciosamente assim que a resposta chega, sem passar por um estado
  // de "carregando" intermediário — troca aceitável por não precisar de
  // uma segunda função/idioma só para esse caso.
  function carregarSolicitacoes() {
    listarSolicitacoes()
      .then((itens) => setSolicitacoes({ itens, carregando: false, erro: null }))
      .catch(() =>
        setSolicitacoes({
          itens: [],
          carregando: false,
          erro: "Não foi possível carregar suas solicitações.",
        })
      );
  }

  useEffect(() => {
    carregarSolicitacoes();
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Link
        to="/minha-conta"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeftIcon className="size-4" />
        Minha Conta
      </Link>

      <h1 className="mb-6 text-2xl font-semibold">Trocas e Devoluções</h1>

      <section className="mb-10 rounded-xl border border-border p-6">
        <h2 className="mb-4 text-lg font-medium">Nova solicitação</h2>
        <NovaSolicitacao onCriada={carregarSolicitacoes} />
      </section>

      <section className="rounded-xl border border-border p-6">
        <h2 className="mb-4 text-lg font-medium">Minhas solicitações</h2>

        {solicitacoes.erro ? (
          <p className="text-sm text-destructive">{solicitacoes.erro}</p>
        ) : solicitacoes.carregando ? (
          <p className="text-sm text-muted-foreground">Carregando...</p>
        ) : solicitacoes.itens.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Você ainda não fez nenhuma solicitação de troca ou devolução.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {solicitacoes.itens.map((solicitacao) => (
              <div
                key={solicitacao.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3"
              >
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium">
                    {solicitacao.produto_nome} - Tam. {solicitacao.produto_tamanho}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Pedido #{solicitacao.pedido_id} ·{" "}
                    {solicitacao.tipo === "troca" ? "Troca" : "Devolução"} ·{" "}
                    {formatarData(solicitacao.criado_em)}
                  </span>
                </div>
                <TrocaDevolucaoStatusBadge status={solicitacao.status} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

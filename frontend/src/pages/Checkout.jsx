import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCart } from "@/contexts/CartContext";
import { enderecoSchema } from "@/schemas/enderecoSchema";
import { listarEnderecos, criarEndereco } from "@/api/enderecos";
import { criarPedido } from "@/api/pedidos";
import { calcularFrete } from "@/api/frete";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatarPreco } from "@/lib/utils";

const NOVO_ENDERECO = "novo";

export default function Checkout() {
  const { itens, totalValor, limparCarrinho } = useCart();
  const navigate = useNavigate();

  const [enderecos, setEnderecos] = useState([]);
  const [enderecosCarregados, setEnderecosCarregados] = useState(false);
  const [enderecoSelecionado, setEnderecoSelecionado] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [erroGeral, setErroGeral] = useState(null);
  const pedidoConfirmadoRef = useRef(false);

  // Opções retornadas pela SuperFrete (uma por transportadora/serviço —
  // normalmente PAC e SEDEX) para o CEP de destino atual, guardadas junto
  // com a `chave` (cep + itens) que gerou o resultado — mesmo padrão de
  // MeusPedidos.jsx/Catalogo.jsx (ver CLAUDE.md): comparar a chave do
  // último resultado contra a chave atual deriva o estado de loading, em
  // vez de um `setFreteCalculando(true)` síncrono no corpo do efeito, que
  // o lint react-hooks/set-state-in-effect não deixa passar.
  const [freteResultado, setFreteResultado] = useState({
    chave: null,
    opcoes: [],
    erro: null,
  });
  // Qual opção o cliente escolheu (id) — interação real do usuário, não dá
  // pra derivar de nada; pré-selecionada na mais barata quando um resultado
  // novo chega (ver o `.then()` do efeito abaixo).
  const [freteSelecionadoId, setFreteSelecionadoId] = useState(null);

  const {
    register,
    trigger,
    getValues,
    control,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(enderecoSchema),
    defaultValues: {
      rua: "",
      numero: "",
      complemento: "",
      bairro: "",
      cidade: "",
      estado: "",
      cep: "",
    },
  });

  useEffect(() => {
    // Ignora quando o carrinho esvaziou por causa de um pedido confirmado com
    // sucesso — senão esse efeito corre com o navigate() de handleConfirmar e
    // manda o usuário de volta pro /carrinho em vez do /pedido-confirmado.
    if (itens.length === 0 && !pedidoConfirmadoRef.current) {
      navigate("/carrinho", {
        replace: true,
        state: {
          mensagem: "Seu carrinho está vazio. Adicione produtos antes de continuar para o checkout.",
        },
      });
    }
  }, [itens.length, navigate]);

  useEffect(() => {
    let ignore = false;

    listarEnderecos()
      .then((data) => {
        if (ignore) return;
        setEnderecos(data);
        setEnderecoSelecionado(data.length > 0 ? data[0].id : NOVO_ENDERECO);
      })
      .catch(() => {
        if (ignore) return;
        setEnderecoSelecionado(NOVO_ENDERECO);
      })
      .finally(() => {
        if (!ignore) setEnderecosCarregados(true);
      });

    return () => {
      ignore = true;
    };
  }, []);

  // `useWatch` (não `getValues`) porque precisa dos re-renders: o efeito de
  // frete abaixo depende de cepNovoEndereco mudar conforme o cliente digita.
  // Preferido a `watch()` (o método retornado por useForm()) porque o React
  // Compiler não consegue memoizar com segurança em torno de `watch()` —
  // `useWatch` é a forma dedicada do react-hook-form pra esse caso exato.
  const cepNovoEndereco = useWatch({ control, name: "cep" });

  const usandoNovoEndereco = enderecoSelecionado === NOVO_ENDERECO;
  // Reaproveita o CEP do endereço já salvo/selecionado em vez de pedir de
  // novo: só precisa perguntar quando o cliente está cadastrando um
  // endereço novo (o formulário já tem um campo cep ali — enderecoSchema).
  const cepDestino = usandoNovoEndereco
    ? cepNovoEndereco
    : enderecos.find((endereco) => endereco.id === enderecoSelecionado)?.cep;
  const cepLimpo = (cepDestino || "").replace(/\D/g, "");
  const cepValido = cepLimpo.length === 8;
  // `null` (não uma string) quando o CEP não está pronto — combinado com
  // freteResultado.chave começando em `null`, isso já garante que
  // `chaveFreteAtual !== freteResultado.chave` seja `false` (logo,
  // freteCalculando `false`) enquanto não houver CEP válido, sem precisar
  // de um estado de loading separado.
  const chaveFreteAtual = cepValido
    ? JSON.stringify({
        cep: cepLimpo,
        itens: itens.map((item) => `${item.variacaoId}:${item.quantidade}`),
      })
    : null;
  const freteCalculando = cepValido && freteResultado.chave !== chaveFreteAtual;

  useEffect(() => {
    if (!cepValido) return;

    let ignore = false;

    calcularFrete(
      cepLimpo,
      itens.map((item) => ({ variacao: item.variacaoId, quantidade: item.quantidade }))
    )
      .then((opcoes) => {
        if (ignore) return;
        const ordenadas = [...opcoes].sort((a, b) => a.preco - b.preco);
        setFreteResultado({ chave: chaveFreteAtual, opcoes: ordenadas, erro: null });
        // Pré-seleciona a mais barata — o cliente ainda pode trocar pra
        // outra opção (ex: SEDEX) na lista abaixo.
        setFreteSelecionadoId(ordenadas[0]?.id ?? null);
      })
      .catch((error) => {
        if (ignore) return;
        // Estratégia deliberada: um erro aqui NÃO bloqueia o checkout (ver
        // handleConfirmar/render abaixo) — a API da SuperFrete é uma
        // dependência externa, e travar toda a compra por causa dela seria
        // pior pro negócio do que aceitar o pedido e combinar o frete
        // manualmente depois. O texto já vem pronto do backend
        // (ServicoIndisponivel/ValidationError — ver CLAUDE.md), com
        // fallback genérico só pra falha de rede.
        setFreteResultado({
          chave: chaveFreteAtual,
          opcoes: [],
          erro:
            error.response?.data?.detail ||
            "Não foi possível calcular o frete. Tente novamente.",
        });
        setFreteSelecionadoId(null);
      });

    return () => {
      ignore = true;
    };
  }, [cepValido, cepLimpo, chaveFreteAtual, itens]);

  if (itens.length === 0) {
    return null;
  }

  // `!freteCalculando && cepValido` implica freteResultado.chave ===
  // chaveFreteAtual (senão freteCalculando seria true) — então é seguro
  // exibir freteResultado.opcoes/erro só nesse caso, sem checar a chave de
  // novo aqui. Evita mostrar o resultado de um CEP anterior enquanto o novo
  // cálculo ainda está em andamento, ou enquanto o CEP está incompleto.
  const freteProntoParaExibir = cepValido && !freteCalculando;
  const freteOpcoesValidas = freteProntoParaExibir ? freteResultado.opcoes : [];
  const freteErroValido = freteProntoParaExibir ? freteResultado.erro : null;
  const freteEscolhido = freteOpcoesValidas.find((opcao) => opcao.id === freteSelecionadoId);
  const freteValor = freteEscolhido?.preco ?? 0;
  const total = totalValor + freteValor;

  async function handleConfirmar() {
    setErroGeral(null);

    if (usandoNovoEndereco) {
      const valido = await trigger();
      if (!valido) return;
    }

    setEnviando(true);

    let enderecoId = enderecoSelecionado;

    if (usandoNovoEndereco) {
      try {
        // `usuario` não precisa mais ser enviado aqui — EnderecoSerializer
        // marca o campo como read_only e o backend sempre o preenche com
        // request.user (ver CLAUDE.md).
        const novoEndereco = await criarEndereco(enderecoSchema.parse(getValues()));
        enderecoId = novoEndereco.id;
      } catch (error) {
        applyApiErrors(error.response?.data, setError, setErroGeral);
        setEnviando(false);
        return;
      }
    }

    try {
      // Pedido + every ItemPedido line are created together in one backend
      // DB transaction (see criarPedido() and CLAUDE.md) — no orphaned
      // Pedido possible if a line fails (e.g. insufficient stock), so
      // there's no rollback call to make here.
      const pedido = await criarPedido({
        endereco: enderecoId,
        itens: itens.map((item) => ({ variacao: item.variacaoId, quantidade: item.quantidade })),
      });

      pedidoConfirmadoRef.current = true;
      limparCarrinho();
      navigate("/pedido-confirmado", { replace: true, state: { pedidoId: pedido.id } });
    } catch (error) {
      setErroGeral(
        error.response?.data?.detail ||
          "Não foi possível concluir o pedido. Verifique se os itens do carrinho ainda têm estoque disponível e tente novamente."
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">Finalizar compra</h1>

      {erroGeral && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {erroGeral}
        </p>
      )}

      <div className="flex flex-col gap-8">
        <section>
          <h2 className="mb-3 text-lg font-medium">Endereço de entrega</h2>

          {!enderecosCarregados ? (
            <p className="text-sm text-muted-foreground">Carregando endereços...</p>
          ) : (
            <div className="flex flex-col gap-3">
              {enderecos.length > 0 && (
                <div className="flex flex-col gap-2">
                  {enderecos.map((endereco) => (
                    <label
                      key={endereco.id}
                      className="flex cursor-pointer items-start gap-2 rounded-md border border-border p-3 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary/5"
                    >
                      <input
                        type="radio"
                        name="endereco"
                        className="mt-1"
                        checked={enderecoSelecionado === endereco.id}
                        onChange={() => setEnderecoSelecionado(endereco.id)}
                      />
                      <span>
                        {endereco.rua}, {endereco.numero}
                        {endereco.complemento ? ` - ${endereco.complemento}` : ""} —{" "}
                        {endereco.bairro}, {endereco.cidade}/{endereco.estado} — CEP {endereco.cep}
                      </span>
                    </label>
                  ))}

                  <label className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name="endereco"
                      checked={usandoNovoEndereco}
                      onChange={() => setEnderecoSelecionado(NOVO_ENDERECO)}
                    />
                    Cadastrar novo endereço
                  </label>
                </div>
              )}

              {usandoNovoEndereco && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label htmlFor="rua">Rua</Label>
                    <Input id="rua" aria-invalid={!!errors.rua} {...register("rua")} />
                    {errors.rua && <p className="text-sm text-destructive">{errors.rua.message}</p>}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="numero">Número</Label>
                    <Input
                      id="numero"
                      inputMode="numeric"
                      aria-invalid={!!errors.numero}
                      {...register("numero")}
                    />
                    {errors.numero && (
                      <p className="text-sm text-destructive">{errors.numero.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="complemento">Complemento</Label>
                    <Input id="complemento" {...register("complemento")} />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="bairro">Bairro</Label>
                    <Input id="bairro" aria-invalid={!!errors.bairro} {...register("bairro")} />
                    {errors.bairro && (
                      <p className="text-sm text-destructive">{errors.bairro.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="cidade">Cidade</Label>
                    <Input id="cidade" aria-invalid={!!errors.cidade} {...register("cidade")} />
                    {errors.cidade && (
                      <p className="text-sm text-destructive">{errors.cidade.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="estado">Estado (UF)</Label>
                    <Input
                      id="estado"
                      maxLength={2}
                      aria-invalid={!!errors.estado}
                      {...register("estado")}
                    />
                    {errors.estado && (
                      <p className="text-sm text-destructive">{errors.estado.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="cep">CEP</Label>
                    <Input id="cep" aria-invalid={!!errors.cep} {...register("cep")} />
                    {errors.cep && <p className="text-sm text-destructive">{errors.cep.message}</p>}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-medium">Frete</h2>
          {freteCalculando ? (
            <p className="text-sm text-muted-foreground">Calculando frete...</p>
          ) : freteErroValido ? (
            <div className="flex flex-col gap-1">
              <p className="text-sm text-destructive">{freteErroValido}</p>
              <p className="text-xs text-muted-foreground">
                Você ainda pode confirmar o pedido — nossa equipe entra em contato para combinar
                o frete.
              </p>
            </div>
          ) : !cepValido ? (
            <p className="text-sm text-muted-foreground">
              Selecione ou cadastre um endereço para calcular o frete.
            </p>
          ) : freteOpcoesValidas.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhuma opção de frete disponível para este CEP.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {freteOpcoesValidas.map((opcao) => (
                <label
                  key={opcao.id}
                  className="flex cursor-pointer items-center justify-between gap-2 rounded-md border border-border p-3 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary/5"
                >
                  <span className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="frete"
                      checked={freteSelecionadoId === opcao.id}
                      onChange={() => setFreteSelecionadoId(opcao.id)}
                    />
                    {opcao.nome} ({opcao.transportadora}) — até {opcao.prazo_dias} dia(s) útil(eis)
                  </span>
                  <span className="font-medium">{formatarPreco(opcao.preco)}</span>
                </label>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-medium">Itens do pedido</h2>
          <div className="flex flex-col gap-3">
            {itens.map((item) => (
              <div key={item.itemId} className="flex items-center justify-between gap-4 text-sm">
                <span>
                  {item.produtoNome} — Tam. {item.tamanho} × {item.quantidade}
                </span>
                <span className="font-medium">{formatarPreco(item.preco * item.quantidade)}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-1 border-t border-border pt-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Subtotal</span>
            <span>{formatarPreco(totalValor)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Frete</span>
            <span>
              {freteCalculando
                ? "Calculando..."
                : freteEscolhido
                  ? formatarPreco(freteEscolhido.preco)
                  : "Não calculado"}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between text-base font-semibold">
            <span>Total</span>
            <span>{formatarPreco(total)}</span>
          </div>
        </section>

        <Button
          type="button"
          size="lg"
          disabled={enviando || freteCalculando}
          onClick={handleConfirmar}
        >
          {enviando ? "Confirmando..." : "Confirmar pedido"}
        </Button>
      </div>
    </div>
  );
}

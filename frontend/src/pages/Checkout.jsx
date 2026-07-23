import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/contexts/CartContext";
import { enderecoSchema } from "@/schemas/enderecoSchema";
import { listarEnderecos, criarEndereco } from "@/api/enderecos";
import { criarPedido, criarItemPedido, deletarPedido } from "@/api/pedidos";
import { applyApiErrors } from "@/lib/apiErrors";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatarPreco } from "@/lib/utils";

// Frete real (SuperFrete) ainda não está integrado — valor simbólico até lá.
const FRETE_PLACEHOLDER = 20;
const NOVO_ENDERECO = "novo";

export default function Checkout() {
  const { user } = useAuth();
  const { itens, totalValor, limparCarrinho } = useCart();
  const navigate = useNavigate();

  const [enderecos, setEnderecos] = useState([]);
  const [enderecosCarregados, setEnderecosCarregados] = useState(false);
  const [enderecoSelecionado, setEnderecoSelecionado] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [erroGeral, setErroGeral] = useState(null);
  const pedidoConfirmadoRef = useRef(false);

  const {
    register,
    trigger,
    getValues,
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

  if (itens.length === 0) {
    return null;
  }

  const usandoNovoEndereco = enderecoSelecionado === NOVO_ENDERECO;
  const total = totalValor + FRETE_PLACEHOLDER;

  async function handleConfirmar() {
    setErroGeral(null);

    if (usandoNovoEndereco) {
      const valido = await trigger();
      if (!valido) return;
    }

    setEnviando(true);

    if (usandoNovoEndereco) {
      try {
        // Endereco.usuario não tem blank=True no model, então o serializer
        // exige o campo mesmo com perform_create() sobrescrevendo-o com
        // request.user logo em seguida — só evita o 400 de validação.
        await criarEndereco({ ...enderecoSchema.parse(getValues()), usuario: user.id });
      } catch (error) {
        applyApiErrors(error.response?.data, setError, setErroGeral);
        setEnviando(false);
        return;
      }
    }

    let pedido;
    try {
      pedido = await criarPedido();
    } catch (error) {
      setErroGeral(
        error.response?.data?.detail || "Não foi possível criar o pedido. Tente novamente."
      );
      setEnviando(false);
      return;
    }

    try {
      for (const item of itens) {
        await criarItemPedido({
          pedido: pedido.id,
          variacao: item.variacaoId,
          quantidade: item.quantidade,
        });
      }

      pedidoConfirmadoRef.current = true;
      limparCarrinho();
      navigate("/pedido-confirmado", { replace: true, state: { pedidoId: pedido.id } });
    } catch (error) {
      // Item falhou no meio do loop — o Pedido ficou órfão. Tenta desfazer
      // (ver CLAUDE.md para o porquê de não ser atômico no backend).
      try {
        await deletarPedido(pedido.id);
      } catch {
        // ignora — cleanup best-effort
      }

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
            <span className="text-muted-foreground">
              Frete (valor temporário — cálculo real em breve)
            </span>
            <span>{formatarPreco(FRETE_PLACEHOLDER)}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-base font-semibold">
            <span>Total</span>
            <span>{formatarPreco(total)}</span>
          </div>
        </section>

        <Button type="button" size="lg" disabled={enviando} onClick={handleConfirmar}>
          {enviando ? "Confirmando..." : "Confirmar pedido"}
        </Button>
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";

// TODO: conteúdo genérico — substituir pela política real de trocas e
// devoluções da Royal Conceito (prazos, condições, processo) antes de
// produção. Página informativa, distinta de TrocasDevolucoes.jsx (o
// formulário de solicitação em si, atrás de PrivateRoute) — esta explica as
// regras ANTES do cliente abrir uma solicitação, então é pública.

export default function PoliticaTrocas() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-semibold">Política de Trocas e Devoluções</h1>
      <p className="mb-6 text-xs text-muted-foreground">
        Conteúdo provisório — prazos e condições a confirmar com a loja.
      </p>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Prazo para solicitar
          </h2>
          <p>
            Você pode solicitar troca ou devolução em até{" "}
            <span className="text-foreground">7 dias corridos</span> após o
            recebimento do produto (prazo placeholder, a confirmar com a
            loja — o mínimo legal previsto pelo Código de Defesa do
            Consumidor para compras online é de 7 dias, contados do
            recebimento).
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Condições do produto
          </h2>
          <p>Para que a troca ou devolução seja aceita, o produto deve estar:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Sem sinais de uso;</li>
            <li>Com a etiqueta original ainda afixada;</li>
            <li>Na embalagem original, quando aplicável.</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Como funciona o processo
          </h2>
          <p>
            Depois de entregue o pedido, abra uma solicitação de troca ou
            devolução informando o pedido, o item e o motivo. Nossa equipe
            analisa o pedido e retorna com as instruções de envio. Após
            recebermos e conferirmos o produto, a troca é processada ou o
            valor é estornado, conforme o tipo de solicitação.
          </p>
          <p className="mt-3">
            <Link
              to="/trocas-e-devolucoes"
              className="text-primary underline-offset-4 hover:underline"
            >
              Abrir uma solicitação de troca ou devolução
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}

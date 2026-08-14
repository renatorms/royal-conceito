// TODO: conteúdo genérico — substituir pelos dados reais de contato da Royal
// Conceito (telefone, WhatsApp, e-mail, endereço das lojas físicas) antes de
// produção. Todos os valores abaixo são placeholders óbvios, escritos apenas
// para a página não ficar vazia enquanto essa informação não é fornecida
// pelo cliente.

export default function Contato() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-semibold">Contato</h1>
      <p className="mb-6 text-xs text-muted-foreground">
        Informações provisórias — pendente dos dados reais da loja.
      </p>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Telefone e WhatsApp
          </h2>
          <p>
            Telefone: <span className="text-foreground">(00) 00000-0000</span>{" "}
            (placeholder, a confirmar)
          </p>
          <p>
            WhatsApp: <span className="text-foreground">(00) 00000-0000</span>{" "}
            (placeholder, a confirmar)
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">E-mail</h2>
          <p>
            <span className="text-foreground">contato@royalconceito.com.br</span>{" "}
            (placeholder, a confirmar)
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Nossas lojas
          </h2>
          <div className="space-y-3">
            <div>
              <p className="font-medium text-foreground">Loja 1</p>
              <p>Endereço da loja 1 — a definir</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Loja 2</p>
              <p>Endereço da loja 2 — a definir</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

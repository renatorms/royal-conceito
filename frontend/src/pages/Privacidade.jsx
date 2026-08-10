// TODO: conteúdo genérico — substituir pelo texto real da Royal Conceito /
// revisão jurídica antes de produção.
//
// ATENÇÃO: esta é uma estrutura PADRÃO de política de privacidade (seções
// comuns em e-commerces brasileiros sob a LGPD), escrita apenas como
// placeholder de desenvolvimento. NÃO tem validade jurídica e NÃO deve ser
// publicada em produção sem revisão de um advogado (ou do cliente) — uma
// política de privacidade real tem implicações legais (o que de fato é
// coletado, com quem é compartilhado, base legal de cada tratamento, prazos
// de retenção, contato real do encarregado/DPO, etc.) que este texto não
// reflete com precisão. Ver CLAUDE.md para o mesmo aviso documentado.

export default function Privacidade() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-semibold">Política de Privacidade</h1>
      <p className="mb-6 text-xs text-muted-foreground">
        Última atualização: conteúdo provisório — pendente de revisão jurídica.
      </p>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            1. Quais dados coletamos
          </h2>
          <p>
            Coletamos dados fornecidos diretamente por você ao criar uma
            conta, realizar um pedido ou entrar em contato conosco, como
            nome, e-mail, endereço de entrega, telefone e dados de pedidos.
            Também podemos coletar dados de navegação (como páginas
            visitadas e produtos visualizados) para melhorar sua experiência
            de compra.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            2. Para que usamos seus dados
          </h2>
          <p>
            Usamos seus dados para processar pedidos, calcular frete,
            viabilizar pagamentos, entrar em contato sobre o andamento de
            uma compra, cumprir obrigações legais e fiscais, e — quando você
            autorizar — enviar comunicações sobre novidades e promoções.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            3. Compartilhamento de dados
          </h2>
          <p>
            Podemos compartilhar dados com parceiros necessários à operação
            da loja, como serviços de cálculo e envio de frete, processadores
            de pagamento e prestadores de serviços de tecnologia, sempre na
            medida necessária para a prestação desses serviços.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            4. Seus direitos como titular dos dados
          </h2>
          <p>Nos termos da Lei Geral de Proteção de Dados (LGPD), você tem direito a:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Confirmação da existência de tratamento de dados;</li>
            <li>Acesso aos seus dados;</li>
            <li>Correção de dados incompletos, inexatos ou desatualizados;</li>
            <li>Anonimização, bloqueio ou eliminação de dados desnecessários;</li>
            <li>Portabilidade dos dados a outro fornecedor de serviço;</li>
            <li>Eliminação dos dados tratados com o seu consentimento;</li>
            <li>Informação sobre compartilhamento de dados com terceiros;</li>
            <li>Revogação do consentimento, a qualquer momento.</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            5. Como entrar em contato
          </h2>
          <p>
            Para exercer seus direitos ou tirar dúvidas sobre esta política,
            entre em contato pelo e-mail{" "}
            <span className="text-foreground">contato@royalconceito.com.br</span>{" "}
            (endereço placeholder, a confirmar).
          </p>
        </section>
      </div>
    </div>
  );
}

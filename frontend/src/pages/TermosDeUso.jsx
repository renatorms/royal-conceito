// TODO: conteúdo genérico — substituir pelo texto real da Royal Conceito /
// revisão jurídica antes de produção.
//
// ATENÇÃO: esta é uma estrutura PADRÃO de termos de uso (seções comuns em
// e-commerces brasileiros), escrita apenas como placeholder de
// desenvolvimento. NÃO tem validade jurídica e NÃO deve ser publicada em
// produção sem revisão de um advogado (ou do cliente) — mesmo tratamento já
// dado a Privacidade.jsx. Ver CLAUDE.md para o mesmo aviso documentado.

export default function TermosDeUso() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-semibold">Termos de Uso</h1>
      <p className="mb-6 text-xs text-muted-foreground">
        Última atualização: conteúdo provisório — pendente de revisão jurídica.
      </p>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            1. Aceitação dos termos
          </h2>
          <p>
            Ao acessar e utilizar o site da Royal Conceito, você concorda
            integralmente com estes Termos de Uso. Caso não concorde com
            qualquer disposição aqui prevista, recomendamos que não utilize
            este site.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            2. Cadastro e responsabilidade do usuário
          </h2>
          <p>
            Ao criar uma conta, você declara que as informações fornecidas
            (nome, e-mail, endereço, telefone, entre outras) são verdadeiras,
            completas e atualizadas. Você é responsável por manter a
            confidencialidade da sua senha e por todas as atividades
            realizadas através da sua conta.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            3. Pedidos, preços e disponibilidade de estoque
          </h2>
          <p>
            Envidamos esforços para manter preços e estoque atualizados, mas
            erros podem ocorrer. A Royal Conceito se reserva o direito de
            cancelar, total ou parcialmente, qualquer pedido em que se
            verifique erro manifesto de preço ou indisponibilidade de
            estoque não identificada a tempo, informando o cliente e
            providenciando o devido estorno quando aplicável.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            4. Propriedade intelectual
          </h2>
          <p>
            Todo o conteúdo deste site — incluindo textos, imagens, logotipos,
            marcas e layout — é de propriedade da Royal Conceito ou de
            terceiros que autorizaram seu uso, sendo protegido pela
            legislação de propriedade intelectual. É vedada a reprodução,
            distribuição ou uso comercial desse conteúdo sem autorização
            prévia e expressa.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            5. Foro e legislação aplicável
          </h2>
          <p>
            Estes Termos de Uso são regidos pela legislação brasileira. Fica
            eleito o foro da comarca do domicílio do consumidor para dirimir
            quaisquer controvérsias decorrentes destes termos, nos termos do
            Código de Defesa do Consumidor.
          </p>
        </section>
      </div>
    </div>
  );
}

// Endereços e WhatsApp das lojas físicas já são os dados reais da Royal
// Conceito. O e-mail continua sendo um placeholder (contato@royalconceito.
// com.br) — substituir pelo contato real antes de produção.

export default function Contato() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-semibold">Contato</h1>
      <p className="mb-6 text-xs text-muted-foreground">
        Endereços e WhatsApp das lojas físicas já são reais — e-mail ainda provisório.
      </p>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <p>
          Ficou com alguma dúvida ou precisa falar com a gente? Estamos à
          disposição pelos canais abaixo.
        </p>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">
            Lojas físicas
          </h2>
          <div className="space-y-3">
            <div>
              <p className="font-medium text-foreground">Loja 1</p>
              <p>
                SIA Trecho 7, Feira dos Importados, Bloco A, Box 259/260,
                Zona Industrial (SIA), Brasília - DF, CEP 71200-070
              </p>
              <p>
                WhatsApp: <span className="text-foreground">(61) 98126-6472</span>
              </p>
            </div>
            <div>
              <p className="font-medium text-foreground">Loja 2</p>
              <p>
                St. de Chácaras QSC 19, Taguatinga, Brasília - DF, CEP
                72017-212
              </p>
              <p>
                WhatsApp: <span className="text-foreground">(61) 98151-5753</span>
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-base font-medium text-foreground">E-mail</h2>
          <p>
            <span className="text-foreground">contato@royalconceito.com.br</span>{" "}
            (placeholder, a confirmar)
          </p>
        </section>

        <p>
          Os endereços e contatos de WhatsApp das lojas físicas acima já são
          reais. O e-mail ainda é provisório e será substituído pelo contato
          real da Royal Conceito antes do lançamento oficial da loja.
        </p>
      </div>
    </div>
  );
}

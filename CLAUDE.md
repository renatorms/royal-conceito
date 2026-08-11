# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Domain documentation

Este arquivo é um índice do projeto e cobre só o que é transversal — mecanismo de autenticação, configuração global, limitações conhecidas para o cliente, e o roadmap geral. Documentação detalhada por domínio vive em arquivos separados; consulte o que corresponder ao que você está mexendo:

- **`docs/produtos.md`** — Categoria/Marca/Produto/Variacao, catálogo, management commands relacionados, Django Admin de produtos.
- **`docs/pedidos.md`** — Pedido/ItemPedido/Endereco/SolicitacaoTrocaDevolucao, checkout, sinais de negócio, frete (SuperFrete), pagamento (InfinitePay), Django Admin de pedidos.
- **`docs/usuarios.md`** — endpoints de conta (registro, dados, senha), PerfilUsuario.
- **`docs/frontend.md`** — toda a arquitetura React/Vite (componentes, páginas, contexts, padrão de formulários, tema visual).
- **`HISTORICO.md`** — narrativas completas de investigação (correções datadas, causa raiz, verificação via curl/shell) para tudo que já foi resolvido. Os arquivos de domínio guardam só um resumo do estado atual + um ponteiro pra cá.

## Documentation Standard

**Ao registrar uma correção ou feature nova, daqui pra frente:** o arquivo de domínio relevante (`docs/produtos.md`, `docs/pedidos.md`, `docs/usuarios.md`, `docs/frontend.md`) recebe um resumo enxuto — o que mudou, por que, e qualquer decisão de design não-óbvia que afete o entendimento futuro do código, tipicamente 3-6 frases. A narrativa completa de investigação (cada teste rodado, cada `curl`, contagens de execução, becos sem saída) vai direto para `HISTORICO.md`, não passa pelo arquivo de domínio primeiro. Isso substitui o padrão anterior (documentar tudo em prosa longa no arquivo principal, mover pra HISTORICO.md só depois, numa faxina posterior) — o objetivo é nunca mais precisar de uma reorganização estrutural como a de 11/08.

## Limitações conhecidas para o cliente

Seção colocada logo no topo do arquivo, de propósito — é a única parte deste documento pensada para leitura rápida antes de uma conversa com o cliente, sem precisar entender código; o resto do arquivo é documentação técnica densa, para consumo do desenvolvedor/da IA. Cada item abaixo já está documentado (com mais detalhe técnico) em algum outro ponto deste arquivo — esta seção só reúne, em português simples, o que já se sabe.

**Dinheiro e prazo de lançamento:**
- **Pagamento:** o sistema já gera um link de pagamento real e confirma o pedido automaticamente quando o cliente paga, mas isso nunca foi testado de ponta a ponta com um pagamento de verdade — só em simulações. Além disso, hoje o link é gerado na conta pessoal de testes do desenvolvedor, não na conta real da loja. **As duas coisas precisam ser resolvidas antes de vender de verdade.**
- **Frete:** o cálculo de frete também usa uma credencial de teste (sandbox) da transportadora parceira. Também precisa trocar pela credencial real antes do lançamento.
- **Imagens dos produtos:** as fotos dos produtos hoje só existem no computador do desenvolvedor — não estão em nenhum servidor. Se o site for publicado hoje, nenhuma imagem de produto vai aparecer. Precisa migrar as imagens para um serviço de hospedagem antes de ir ao ar.
- **Textos institucionais:** as páginas "Quem Somos" e "Política de Privacidade" (rodapé do site) têm só texto genérico de exemplo, não o texto real da loja. **A Política de Privacidade em especial não pode ir ao ar como está** — ela tem implicação jurídica real (o que a loja diz que faz com os dados do cliente) e precisa ser revisada por um advogado ou pelo próprio cliente antes do lançamento.
- **Produtos de teste no catálogo:** existem hoje cerca de 124 produtos fictícios no banco, com nome começando em "[TESTE]", criados só para os menus de navegação do site terem o que mostrar durante o desenvolvimento. Eles aparecem no catálogo normalmente e precisam ser apagados antes do lançamento (à medida que produtos reais forem cadastrados nas mesmas marcas/categorias).

**Uso do dia a dia (o cliente/quem administra o catálogo precisa saber):**
- **Categoria nova não aparece sozinha no menu do topo:** quando uma Categoria nova é criada pelo Admin, ela não aparece automaticamente nos menus "Roupas"/"Calçados"/"Acessórios" no topo do site — é preciso avisar o desenvolvedor para incluir o nome dela numa lista fixa no código primeiro. Sem isso, a categoria existe e pode ser vendida, só não aparece nesse menu específico.
- **Produto só aparece no menu do topo com categoria E marca preenchidas:** não basta preencher só uma das duas — um produto sem marca (ou sem categoria) definida não vai aparecer nesses menus de navegação, mesmo que já esteja à venda e apareça na busca/catálogo normal.
- **"Promoções" ainda não existe:** o sistema hoje não tem nenhum jeito de marcar um produto como "em promoção" ou dar desconto — por isso não existe (e não vai aparecer sozinho) um item de "Promoções" no menu do site.
- **Cadastro duplicado por e-mail:** hoje é possível duas contas diferentes se cadastrarem com o mesmo e-mail (o sistema só impede um cliente de *trocar* o e-mail de uma conta já existente para um que já está em uso por outra).

**Polimento visual pendente (nada quebrado, só falta acabamento):**
- O cabeçalho do site ainda é uma versão inicial — em telas bem estreitas (celular pequeno), os links do canto direito (Meus Pedidos, carrinho, login) podem se apertar/sobrepor.
- O site só tem o tema escuro por enquanto, sem opção de alternar para um tema claro.

## Project Overview

Royal Conceito — an e-commerce backend for a clothing store, built with Django 6 + Django REST Framework. Brazilian Portuguese is used for model/field names and UI. The frontend (React/Vite) is under active development (Phase 4) in `frontend/`.

## Common Commands

All commands run from `backend/`:

```bash
# Activate virtualenv
source .venv/bin/activate

# Run dev server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test
python manage.py test produtos    # single app

# Create admin user
python manage.py createsuperuser

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Monolithic Django project** with three apps under `backend/`:

- **core/** — Project settings, root URL config, JWT token endpoints
- **produtos/** — Product catalog (Categoria, Marca, Produto, Variacao)
- **pedidos/** — Order processing (Pedido, ItemPedido, Endereco) + business logic signals
- **usuarios/** — User registration (uses Django's built-in User model)


Para o modelo de dados e as regras de negócio de cada domínio (Produto/Variacao, Pedido/ItemPedido/Endereco, PerfilUsuario), veja `docs/produtos.md`, `docs/pedidos.md`, `docs/usuarios.md` respectivamente.

### Data Flow

```
HTTP Request → DRF Router → ViewSet → Serializer → Model/ORM → Signal → SQLite
```

All API endpoints use DRF's `DefaultRouter` with `ModelViewSet`. Each app registers its own router in its `urls.py`, and `core/urls.py` includes them all under `/api/`.

### Authentication mechanism

O mecanismo de autenticação abaixo é usado por toda a API — quem usa qual `Permission`/`ViewSet` específico está documentado no arquivo de domínio correspondente (`docs/produtos.md`, `docs/pedidos.md`, `docs/usuarios.md`).

- JWT via `djangorestframework-simplejwt`, delivered as **httpOnly cookies** rather than `Authorization: Bearer` headers
  - `core/views.py::ThrottledTokenObtainPairView` (`POST /api/token/`, throttled `throttle_scope = "login"`) sets `access_token` (`Path=/`) and `refresh_token` (`Path=/api/token/refresh/`) cookies from the simplejwt response and strips them out of the JSON body; it also calls `get_token(request)` so a readable `csrftoken` cookie is issued at login
  - `core/views.py::CookieTokenRefreshView` (`POST /api/token/refresh/`) reads `refresh_token` from `request.COOKIES`, builds simplejwt's serializer directly via `self.get_serializer(data={"refresh": refresh_token})` (avoiding the private `request._full_data` attribute), and re-sets the rotated cookies from `serializer.validated_data`
  - `core/views.py::LogoutView` (`POST /api/logout/`, `IsAuthenticated`) clears both cookies via `response.delete_cookie()` using matching paths
  - `core/authentication.py::CookieJWTAuthentication` (registered as the sole `DEFAULT_AUTHENTICATION_CLASSES`) reads the JWT from `request.COOKIES.get("access_token")` instead of the `Authorization` header, and enforces CSRF (mirroring DRF's `SessionAuthentication.enforce_csrf`) on every authenticated request — the browser sends the JWT cookie automatically, so all state-changing requests (checkout, order creation, admin writes, logout) require a valid `X-CSRFToken` header matching the `csrftoken` cookie
  - Cookies use `secure=not settings.DEBUG` and `samesite="Lax"`; `CORS_ALLOW_CREDENTIALS = True` and `CSRF_TRUSTED_ORIGINS` (env var, defaults to `http://localhost:5173`) are required for the cross-origin Vite frontend to send/receive them
- Default permission: `IsAuthenticated` (all endpoints require the cookie-based token)
- Token endpoints: `POST /api/token/` (obtain, throttled), `POST /api/token/refresh/` (refresh), `POST /api/logout/` (clears cookies, requires auth)

### Rate Limiting

- `DEFAULT_THROTTLE_CLASSES` = `ScopedRateThrottle`; only views with a `throttle_scope` attribute are throttled, so the rest of the API is unaffected
- `/api/token/` (`core/views.py::ThrottledTokenObtainPairView`, `throttle_scope = "login"`) and `/api/registro/` (`throttle_scope = "registro"`) are limited to 5 requests/min per client via `DEFAULT_THROTTLE_RATES` in `core/settings.py`
- `/api/frete/calcular/` (`throttle_scope = "frete"`) is limited to 20 requests/min — see "SuperFrete Shipping Integration" in `docs/pedidos.md` for why this endpoint is both public and throttled, same shape as `/api/token/`/`/api/registro/`

### Environment Variables

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` are loaded via `python-decouple` (`core/settings.py`) instead of being hardcoded
- Local values live in `backend/.env` (gitignored); `backend/.env.example` documents the expected variables
- `CORS_ALLOW_ALL_ORIGINS` is tied to `DEBUG` — all origins allowed only in dev; in production only origins listed in `CORS_ALLOWED_ORIGINS` are accepted
- Variáveis específicas de domínio (`SUPERFRETE_*`, `INFINITEPAY_*`) estão documentadas em `docs/pedidos.md`, junto com a integração que cada uma serve.

## API Endpoints

| Prefix | App | Endpoints |
|--------|-----|-----------|
| `/api/categorias/` | produtos | CRUD categories |
| `/api/marcas/` | produtos | CRUD brands |
| `/api/produtos/` | produtos | CRUD products (nested variacoes) |
| `/api/variacoes/` | produtos | CRUD size variants |
| `/api/menu/categorias/` | produtos | Categoria→Marcas structure for the Header nav (Tênis/Roupas/Acessórios) (public) |
| `/api/pedidos/` | pedidos | CRUD orders (nested itens) |
| `/api/pedidos/{id}/gerar-link-pagamento/` | pedidos | Generates an InfinitePay checkout link for the order (owner/staff only) |
| `/api/pedidos/webhook-infinitepay/` | pedidos | InfinitePay payment-confirmation webhook (public, throttled) |
| `/api/itens/` | pedidos | CRUD order items (triggers stock signals) |
| `/api/enderecos/` | pedidos | CRUD addresses |
| `/api/frete/calcular/` | pedidos | Shipping quote via SuperFrete (public, throttled) |
| `/api/trocas-devolucoes/` | pedidos | CRUD troca/devolução requests (create requires the item's `Pedido` to be `entregue`; `status` read-only for all clients) |
| `/api/registro/` | usuarios | User registration |
| `/api/me/` | usuarios | Current authenticated user (`GET`); `PATCH` updates `email`/`telefone` (id, username, email, is_staff, telefone) |
| `/api/me/senha/` | usuarios | Change password (`senha_atual`/`nova_senha`, `IsAuthenticated`) |
| `/api/token/` | core | JWT obtain (sets httpOnly cookies) |
| `/api/token/refresh/` | core | JWT refresh (reads/sets httpOnly cookies) |
| `/api/logout/` | core | Clears JWT cookies |

## DRF Configuration

- Pagination: `PageNumberPagination`, 10 items per page
- Filter backends: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Auth: `core.authentication.CookieJWTAuthentication` (JWT read from the `access_token` cookie, not the `Authorization` header; enforces CSRF on authenticated requests)
- Throttling: `ScopedRateThrottle`, applied only to `/api/token/` and `/api/registro/` (5/min each)
- CORS: all origins allowed only when `DEBUG=True`; restricted to `CORS_ALLOWED_ORIGINS` in production; `CORS_ALLOW_CREDENTIALS = True` so the frontend can send/receive the auth cookies cross-origin

## Not yet done (visão geral — detalhe completo em cada docs/*.md)

- **Produtos:** `[TESTE]` fixture products precisam ser deletados antes de produção; imagens de produto ainda não têm hospedagem real. Ver "Pendências" em `docs/produtos.md`.
- **Pedidos:** `INFINITEPAY_HANDLE` ainda é a conta pessoal do desenvolvedor; webhook da InfinitePay nunca testado ponta-a-ponta com pagamento real; credencial SuperFrete ainda é sandbox; Trocas/Devoluções tem dois limites de escopo conhecidos. Ver "Pendências" em `docs/pedidos.md`.
- **Frontend:** `/privacidade` tem conteúdo genérico e **não pode ir ao ar como está** — precisa revisão jurídica antes de produção; `/sobre` também é texto placeholder; Header ainda não tem tratamento responsivo completo no cluster de ações à direita. Ver as entradas de `Sobre.jsx`/`Privacidade.jsx`/`Header.jsx` em `docs/frontend.md`.

## Development Status

- Backend: 100% complete
  - Phase 1 (Backend MVP): Complete
  - Phase 2 (REST API): Complete
  - Phase 3 (JWT Auth): Complete
- Phase 4 (React Frontend): In progress
  - Done: Axios client with CSRF header injection and single-flight refresh-on-401 interceptor; `AuthContext` (`login`/`register`/`logout`/session hydration via `/api/me/`); `PrivateRoute` guard (preserves attempted route via `state.from`); backend `/api/me/` endpoint; real `/login` and `/registro` forms (`react-hook-form` + `zod`, shared `applyApiErrors` helper — the pattern for all future forms); minimal `Header` with login/logout and a cart badge; product catalog (`Catalogo.jsx` at `/`, filters/search/ordering/pagination synced to the URL) and product detail page (`ProdutoDetalhe.jsx` at `/produtos/:id`), backed by `src/api/produtos.js`; frontend-only shopping cart (`CartContext.jsx`, `localStorage`-backed) with size/quantity selection wired up on the product page and a `/carrinho` page (public) to review/edit/remove lines; first checkout pass (`/checkout`, `PrivateRoute`) — reuse-or-create address, read-only order summary, Pedido + ItemPedido creation chained against the real API, placeholder shipping value, `/pedido-confirmado` landing page; order history (`MeusPedidos.jsx` at `/meus-pedidos`, `PedidoDetalhe.jsx` at `/meus-pedidos/:id`, both `PrivateRoute`), backed by new `listarPedidos()`/`buscarPedido()` in `src/api/pedidos.js`, with a shared `PedidoStatusBadge` component; saved-address management (`MeusEnderecos.jsx` at `/meus-enderecos`, `PrivateRoute`) — list, inline edit, delete (with confirm), and create, backed by new `atualizarEndereco()`/`deletarEndereco()` in `src/api/enderecos.js` and a shared `EnderecoForm` component (extracted from `Checkout.jsx`'s address form); orders now record which address they shipped to (`Pedido.endereco` FK, `PedidoDetalhe.jsx` displays it) instead of only saving the address to the account. Alongside this frontend work, several backend correctness issues surfaced while building checkout were fixed at the source rather than just worked around: insufficient-stock and delete-blocked-by-`PROTECT` errors now return clean `400`s instead of unhandled `500`s; `Pedido`+`ItemPedido` creation is now atomic in one backend transaction (`itens_criacao`, replacing the old create-then-loop flow, with `Checkout.jsx` updated to match); a stock-decrement race condition across concurrent requests was closed (`select_for_update()` + an atomic conditional update, validated with a real threading test since Postgres wasn't available to test against); and the Django Admin no longer lets staff manually override the server-computed `preco_unitario`/`subtotal`/`total` fields — see "Backend quirks" and "Django Admin" in `docs/pedidos.md` for details. Real shipping cost via SuperFrete (`src/api/frete.js`, `Checkout.jsx`) replaced the fixed placeholder — see "SuperFrete Shipping Integration" in `docs/pedidos.md` for the full design (backend client/endpoint, CEP reuse from the address, auto-recalculation, and the deliberate choice not to hard-block checkout if the quote fails). The chosen freight option is now persisted as a frozen snapshot on `Pedido` (`frete_valor`/`frete_nome`/`frete_transportadora`/`frete_prazo_dias`) and included in `Pedido.total`, closing the gap this section used to note as open — see "Key Model Relationships"/"Business Logic via Signals" in `docs/pedidos.md` and `PedidoDetalhe.jsx` (displays it when present, `docs/frontend.md`). Real payment via InfinitePay (`src/api/pedidos.js::gerarLinkPagamento()`, `Checkout.jsx`, `PedidoConfirmado.jsx`) replaced the old "create Pedido, skip straight to confirmation" flow — see "InfinitePay Payment Integration" in `docs/pedidos.md` for the full design (separate link-generation action, webhook with `payment_check`-based verification since InfinitePay signs nothing, retry-without-recreating-the-order on a failed link generation). A real account-management page (`Perfil.jsx` at `/perfil`, added 08/08) rounds out "Área do Cliente" alongside `MeusPedidos.jsx`/`MeusEnderecos.jsx` — editable email (backend gained `PATCH /api/me/`, `username` deliberately kept immutable) plus a recent-orders summary linking into the existing order-history/address pages rather than duplicating them; reachable via a new "Perfil" link added to the `Header.jsx` account dropdown. **Restructured 10/08 into a real "Área do Cliente" hub**, replacing that single `Perfil.jsx` page: `MinhaConta.jsx` (`/minha-conta`) is now the one entry point off the Header's account icon (a plain `Link`, the dropdown removed entirely — see `Header.jsx` above), listing `Meus Pedidos`/`Informações da Conta`/`Meus Endereços`/`Trocas e Devoluções` plus a `Sair` action; email/telefone editing and a new "Alterar senha" form moved to `MinhaContaDados.jsx` (`/minha-conta/dados`). Backend gained a `telefone` field (new `PerfilUsuario` model, `usuarios/models.py` — the `usuarios` app's first real model — `OneToOneField` to `User`, `PATCH /api/me/` now accepts it alongside `email`) and a real password-change endpoint (`POST /api/me/senha/`, validates the current password via `check_password()` and the new one via Django's own `validate_password()`). A genuinely new feature, not placeholder scaffolding, rounds out this pass: **Trocas e Devoluções** (`/trocas-e-devolucoes`) — new `SolicitacaoTrocaDevolucao` model (`pedidos` app), a `ModelViewSet` at `/api/trocas-devolucoes/` enforcing the core rule that a request can only be opened against an already-`entregue` order, and a page to file a new request (Pedido → Item → tipo → motivo, cascading selects) and see past ones with a status badge. See "Key Model Relationships"/"Authentication & Authorization" in `docs/pedidos.md`/`docs/usuarios.md` and the `MinhaConta.jsx`/`MinhaContaDados.jsx`/`TrocasDevolucoes.jsx` entries in `docs/frontend.md` for the full design of all of this.
  - Remaining: full styled header (see "Not yet done" above); swapping `INFINITEPAY_HANDLE` for the client's real account and exercising the InfinitePay webhook end-to-end against a real payment before production (see "Not yet done" above)
- Visual Polish phase: Started 07/08 — three steps done so far, all the same day: (1) the real Royal Conceito brand theme (dark-by-default, gold accent) replaced the neutral shadcn placeholder palette used throughout Phase 4 so far — see the "Brand theme" entry near the top of `docs/frontend.md` for the full design; (2) a first Header mega menu (`MegaMenu.jsx`, a single catch-all "Categorias" trigger) — since superseded by (3); (3) the same-day Header redesign — `MegaMenu.jsx` deleted and replaced by a full central nav (originally **Tênis | Roupas | Acessórios | Marcas | busca**; restructured 08/08 to **Calçados | Roupas | Acessórios | Marcas | busca** once "Tênis" needed to also cover the new "Sandálias" categoria — see the `HeaderNav.jsx` entry in `docs/frontend.md` for that follow-up, `HeaderNav.jsx` + the reusable `NavDropdown.jsx` shell) inside a proper 3-column `Header.jsx` layout (logo / centered nav / actions) — see the `Header.jsx`/`NavDropdown.jsx`/`HeaderNav.jsx` entries in `docs/frontend.md` for the full design, including the documented per-group name-matching limitation and why "Marcas" is a flat list rather than a mega-menu grid. **"Promoções" was deliberately left out of this nav** — `Produto` has no discount/promotion concept in the schema at all today, and adding a real one (new field(s) on `Produto`? a separate promotions model? how "in promotion" gets computed) is a data-model decision that doesn't belong inside a Header redesign; a nav item that linked to nothing meaningful was rejected rather than built as a placeholder. Still open from earlier steps at the time: `PedidoStatusBadge.jsx`'s hardcoded light-mode pill colors reading oddly against the new dark background, and the right-hand actions cluster in `Header.jsx` (Meus Pedidos/Meus Endereços/carrinho/login) still having no responsive wrapping of its own (noted under "Header.jsx", still open). **The status-badge item is now closed — fixed 11/08, see the dedicated bullet under "Brand theme" in `docs/frontend.md`** (also covered `TrocaDevolucaoStatusBadge.jsx`, added 10/08, which had copied the same light-mode pattern). No light/dark toggle yet — dark is the only theme for now. (4) Added 10/08: first `Footer.jsx`, plus two new public institutional pages it links to (`/sobre`, `/privacidade`) — see the entries above. `/sobre`'s and `/privacidade`'s content are both placeholders; `/privacidade`'s specifically **blocks production** until a lawyer or the client reviews it (see "Not yet done" above).
- Phase 5 (Deploy + PostgreSQL): Planned. **Blocked on a product-image hosting decision** — see "Not yet done" above and the `Produto.imagem_url` entry in `docs/produtos.md`: the 115 real product photos live only in `frontend/public/produtos/` on the developer's machine today, not in Git, and Cloudflare Pages (the chosen frontend host) builds from Git — deploying before this is resolved ships a storefront with every product image broken.

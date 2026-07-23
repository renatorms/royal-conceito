# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### Data Flow

```
HTTP Request → DRF Router → ViewSet → Serializer → Model/ORM → Signal → SQLite
```

All API endpoints use DRF's `DefaultRouter` with `ModelViewSet`. Each app registers its own router in its `urls.py`, and `core/urls.py` includes them all under `/api/`.

### Key Model Relationships

- **Produto** → has many **Variacao** (size variants with stock tracking, CASCADE)
- **Produto** → belongs to **Marca** and **Categoria** (both SET_NULL)
- **Pedido** → has many **ItemPedido** (CASCADE), belongs to **User** via `usuario` FK (PROTECT — can't delete a user with existing orders)
- **ItemPedido** → references **Variacao** (PROTECT — can't delete sold variants); `subtotal` is persisted on the model (not computed on the fly)
- **Variacao** has `unique_together = ["produto", "tamanho"]`
- **Endereco** → belongs to **User** via `usuario` FK (CASCADE — deleting a user deletes their addresses)

### Business Logic via Signals

`pedidos/signals.py` contains one `pre_save` and three `post_save`/`post_delete` signals registered in `pedidos/apps.py`, all wrapped in `@transaction.atomic`:

1. **calcula_subtotal** (`pre_save`) — On ItemPedido save: sets `subtotal = quantidade × preco_unitario` before it's persisted.
2. **diminui_estoque** (`post_save`) — On ItemPedido creation: validates stock availability, decrements Variacao.estoque. Raises `ValueError` on insufficient stock.
3. **atualiza_total_pedido** (`post_save`) — On ItemPedido save: recalculates Pedido.total as sum of ItemPedido.subtotal.
4. **atualiza_total_ao_deletar** (`post_delete`) — On ItemPedido delete: recalculates Pedido.total.

### Authentication & Authorization

- JWT via `djangorestframework-simplejwt`, delivered as **httpOnly cookies** rather than `Authorization: Bearer` headers
  - `core/views.py::ThrottledTokenObtainPairView` (`POST /api/token/`, throttled `throttle_scope = "login"`) sets `access_token` (`Path=/`) and `refresh_token` (`Path=/api/token/refresh/`) cookies from the simplejwt response and strips them out of the JSON body; it also calls `get_token(request)` so a readable `csrftoken` cookie is issued at login
  - `core/views.py::CookieTokenRefreshView` (`POST /api/token/refresh/`) reads `refresh_token` from `request.COOKIES`, builds simplejwt's serializer directly via `self.get_serializer(data={"refresh": refresh_token})` (avoiding the private `request._full_data` attribute), and re-sets the rotated cookies from `serializer.validated_data`
  - `core/views.py::LogoutView` (`POST /api/logout/`, `IsAuthenticated`) clears both cookies via `response.delete_cookie()` using matching paths
  - `core/authentication.py::CookieJWTAuthentication` (registered as the sole `DEFAULT_AUTHENTICATION_CLASSES`) reads the JWT from `request.COOKIES.get("access_token")` instead of the `Authorization` header, and enforces CSRF (mirroring DRF's `SessionAuthentication.enforce_csrf`) on every authenticated request — the browser sends the JWT cookie automatically, so all state-changing requests (checkout, order creation, admin writes, logout) require a valid `X-CSRFToken` header matching the `csrftoken` cookie
  - Cookies use `secure=not settings.DEBUG` and `samesite="Lax"`; `CORS_ALLOW_CREDENTIALS = True` and `CSRF_TRUSTED_ORIGINS` (env var, defaults to `http://localhost:5173`) are required for the cross-origin Vite frontend to send/receive them
- Default permission: `IsAuthenticated` (all endpoints require the cookie-based token)
- `produtos` ViewSets (Categoria, Marca, Produto, Variacao) use `IsAdminOrReadOnly` (`produtos/permissions.py`) — reads are public, writes require `request.user.is_staff`
- `PedidoViewSet` uses `IsAuthenticated` + `IsDonorOrStaff` (`pedidos/permissions.py`) and filters `get_queryset()` so non-staff users only see their own orders (staff see all); `perform_create()` auto-assigns `usuario` from `request.user`, so clients never submit it
- `EnderecoViewSet` uses `IsAuthenticated` + `IsDonorOrStaff`, filters `get_queryset()` by `usuario=request.user` (staff see all), and `perform_create()` forces `usuario=request.user` — closes an IDOR that let any authenticated user read/edit/delete another user's address
- `ItemPedidoViewSet` uses `IsAuthenticated` + `IsItemDonorOrStaff` (`pedidos/permissions.py`), filters `get_queryset()` by `pedido__usuario=request.user` (staff see all); `perform_create()` raises `PermissionDenied` (403) if a non-staff user targets a `Pedido` they don't own, and always sets `preco_unitario` server-side from `variacao.produto.preco` — the field is `read_only` on `ItemPedidoSerializer`, so clients can't forge a price or attach items to someone else's order
- `/api/registro/` uses `AllowAny`
- `usuarios/views.py::MeView` (`GET /api/me/`, `IsAuthenticated`) returns the current user via `MeSerializer` (id, username, email, is_staff) — used by the frontend to hydrate/validate the session on load and after login
- Token endpoints: `POST /api/token/` (obtain, throttled), `POST /api/token/refresh/` (refresh), `POST /api/logout/` (clears cookies, requires auth)

### Rate Limiting

- `DEFAULT_THROTTLE_CLASSES` = `ScopedRateThrottle`; only views with a `throttle_scope` attribute are throttled, so the rest of the API is unaffected
- `/api/token/` (`core/views.py::ThrottledTokenObtainPairView`, `throttle_scope = "login"`) and `/api/registro/` (`throttle_scope = "registro"`) are limited to 5 requests/min per client via `DEFAULT_THROTTLE_RATES` in `core/settings.py`

### Environment Variables

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` are loaded via `python-decouple` (`core/settings.py`) instead of being hardcoded
- Local values live in `backend/.env` (gitignored); `backend/.env.example` documents the expected variables
- `CORS_ALLOW_ALL_ORIGINS` is tied to `DEBUG` — all origins allowed only in dev; in production only origins listed in `CORS_ALLOWED_ORIGINS` are accepted

### Query Optimization

`ProdutoViewSet` uses `select_related("marca", "categoria").prefetch_related("variacoes")` to avoid N+1 queries, with a default `order_by("nome")` so pagination is always deterministic (avoids `UnorderedObjectListWarning`); clients can still override via the `ordering` query param (`ordering_fields`: nome, preco). Supports `filterset_fields`, `search_fields` (nome, marca__nome).

### Django Admin

`pedidos/admin.py` customizes the admin for order management:

- **PedidoAdmin** — `list_display` (id, usuario, status, total, data_pedido), `list_filter` (status, data_pedido), `search_fields` (usuario__username), with an `ItemPedidoInline` to view/edit order items directly on the order page
- **ItemPedidoAdmin** — `list_display` (pedido, variacao, quantidade, preco_unitario, subtotal), `list_filter` (pedido__status)
- **EnderecoAdmin** — `list_display` (usuario, rua, cidade, estado)

## API Endpoints

| Prefix | App | Endpoints |
|--------|-----|-----------|
| `/api/categorias/` | produtos | CRUD categories |
| `/api/marcas/` | produtos | CRUD brands |
| `/api/produtos/` | produtos | CRUD products (nested variacoes) |
| `/api/variacoes/` | produtos | CRUD size variants |
| `/api/pedidos/` | pedidos | CRUD orders (nested itens) |
| `/api/itens/` | pedidos | CRUD order items (triggers stock signals) |
| `/api/enderecos/` | pedidos | CRUD addresses |
| `/api/registro/` | usuarios | User registration |
| `/api/me/` | usuarios | Current authenticated user (id, username, email, is_staff) |
| `/api/token/` | core | JWT obtain (sets httpOnly cookies) |
| `/api/token/refresh/` | core | JWT refresh (reads/sets httpOnly cookies) |
| `/api/logout/` | core | Clears JWT cookies |

## DRF Configuration

- Pagination: `PageNumberPagination`, 10 items per page
- Filter backends: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Auth: `core.authentication.CookieJWTAuthentication` (JWT read from the `access_token` cookie, not the `Authorization` header; enforces CSRF on authenticated requests)
- Throttling: `ScopedRateThrottle`, applied only to `/api/token/` and `/api/registro/` (5/min each)
- CORS: all origins allowed only when `DEBUG=True`; restricted to `CORS_ALLOWED_ORIGINS` in production; `CORS_ALLOW_CREDENTIALS = True` so the frontend can send/receive the auth cookies cross-origin

## Frontend (`frontend/`)

React 19 + Vite + Tailwind + shadcn/ui, using `react-router-dom` for routing.

- **`src/lib/axios.js`** — shared Axios instance (`api`), `baseURL` from `VITE_API_URL` (defaults to `http://localhost:8000/api`), `withCredentials: true` so the httpOnly JWT/CSRF cookies flow cross-origin
  - Request interceptor attaches `X-CSRFToken` (read from the `csrftoken` cookie) on state-changing methods (`post`, `put`, `patch`, `delete`), matching the backend's CSRF enforcement
  - Response interceptor catches a `401`, calls `POST /token/refresh/` once (deduped via a module-level `isRefreshing`/`refreshPromise` pair so concurrent 401s share a single refresh call), then retries the original request; requests already flagged `_retry`, or the refresh call itself, are not retried again to avoid loops
- **`src/contexts/AuthContext.jsx`** — `AuthProvider` + `useAuth()` hook; on mount calls `GET /me/` to hydrate `user` (`isLoading` covers this initial check); exposes `login(username, password)` (`POST /token/`, then `GET /me/`), `register(dados)` (`POST /registro/`), and `logout()` (`POST /logout/`, always clears local `user`); `isAuthenticated` is derived as `!!user`; on failure, both `login` and `register` resolve `{ success: false, error }` where `error` is the raw DRF error payload (`{ detail }` or `{ campo: [...] }`), not a pre-extracted string — kept raw so callers can map it onto a form (see `src/lib/apiErrors.js`)
- **`src/contexts/CartContext.jsx`** — `CartProvider` + `useCart()` hook; cart state (`itens`) is frontend-only — loaded from and persisted to `localStorage` (key `"carrinho"`, via a `useEffect` on every change) — with no backend persistence until a `Pedido` is created at checkout; each item is keyed by `variacaoId` (a `Variacao` already belongs to exactly one `Produto`, so it's a sufficient unique key) and carries a snapshot of `estoque` taken when added; exposes `adicionarItem(produto, variacao, quantidade)` (merges into an existing line for the same `variacaoId` instead of duplicating), `removerItem(itemId)`, `atualizarQuantidade(itemId, novaQuantidade)` (clamped to `[1, estoque]` — dropping to 0 removes the line rather than leaving a zero-quantity row), `limparCarrinho()`, and derived `totalItens`/`totalValor`
- **`src/components/PrivateRoute.jsx`** — route guard using `useAuth()`; renders a loading state while `isLoading`, redirects to `/login` (via `Navigate replace`, passing `state={{ from: location }}`) when not authenticated, otherwise renders the nested route (`Outlet`)
- **`src/App.jsx`** — wraps the app in `AuthProvider` + `CartProvider` (independent of each other, order doesn't matter) + `BrowserRouter`, renders `Header` above `Routes`. Routes: `/` (`Catalogo`, product grid), `/produtos/:id` (`ProdutoDetalhe`), `/carrinho` (`Carrinho`, public — no `PrivateRoute`), `/login` and `/registro` (real forms, see below), and `/meus-pedidos` behind `PrivateRoute` (placeholder); `/checkout` is linked from the cart but has no route yet (next roadmap item)
- **`src/components/Header.jsx`** — minimal/temporary header (full styling later): shows the logged-in username + a "Sair" button (`logout()` then redirect home) when authenticated, or a "Login" link otherwise; also shows a cart icon linking to `/carrinho` with a badge (`useCart().totalItens`, hidden at 0), visible regardless of auth state
- **Forms (`react-hook-form` + `zod`, via `@hookform/resolvers/zod`)** — the established pattern for all forms in this project (login/registro now, endereço/checkout later):
  - One schema file per form in `src/schemas/` (e.g. `loginSchema.js`, `registroSchema.js`); cross-field validation (e.g. password confirmation) uses Zod's `.refine()` with an explicit `path`
  - `src/lib/apiErrors.js::applyApiErrors(errorData, setError, setGeneralError)` — shared helper that maps a DRF error payload onto the form: `{ detail }` → general banner via `setGeneralError`, `{ campo: ["msg"] }` → per-field via react-hook-form's `setError`; reuse this for every new form instead of writing bespoke error-mapping
  - `src/pages/Login.jsx` and `src/pages/Registro.jsx` are the reference implementation of the pattern (schema + `useForm({ resolver: zodResolver(schema) })` + `applyApiErrors` on failure)
- **`src/components/ui/input.jsx`, `src/components/ui/label.jsx`** — plain shadcn-style form primitives (native `<input>`/`<label>`, not base-ui primitives) added alongside the existing `button.jsx`
- **`src/api/`** — one function-per-resource module per REST resource, using the shared `api` axios instance; `produtos.js` is the first one: `listarProdutos({ categoria, marca, search, ordering, page })`, `buscarProduto(id)`, `listarCategorias()`, `listarMarcas()` — the last two follow the API's `next` link to the end since `/categorias/` and `/marcas/` are paginated too (10/page) and the catalog currently has more than 10 of each
- **`src/pages/Catalogo.jsx`** (route `/`) — product grid consuming `/api/produtos/`; search (debounced 400ms), categoria/marca filters, price ordering, and pagination (via `count`/`next`/`previous`) are all synced to the URL through `useSearchParams`, so filtered views are shareable links and work with browser back/forward
- **`src/pages/ProdutoDetalhe.jsx`** (route `/produtos/:id`) — single product view (marca, nome, categoria, preço, variações); out-of-stock sizes are shown alongside in-stock ones with a disabled/"Esgotado" treatment rather than being omitted; in-stock sizes are clickable buttons (`aria-pressed`), selecting one reveals a quantity stepper (`+`/`-`, clamped to `[1, estoque]`) and enables "Adicionar ao carrinho" (`useCart().adicionarItem`), which shows "Adicionado!" for 1.5s as feedback
- **`src/pages/Carrinho.jsx`** (route `/carrinho`, public) — lists cart lines (`useCart().itens`) with placeholder image, product name (linking back to `/produtos/:id`), tamanho, unit price, a quantity stepper wired to `atualizarQuantidade` (the `+` button disables at `estoque`), per-line subtotal, and a remove button (`removerItem`); shows an empty-state message + link to the catalog when `itens` is empty; ends with the running total and a "Finalizar compra" button linking to `/checkout` (not implemented yet)
- **`src/components/ProdutoCard.jsx`, `src/components/ProdutoImagemPlaceholder.jsx`** — product card and a fixed placeholder image reused for every product (the backend has no product image field yet)
- **`src/components/ui/select.jsx`, `src/components/ui/card.jsx`** — added via the `shadcn` CLI (same `style: base-vega` as the existing `button.jsx`/`input.jsx`) for the catalog filters and product cards
- `.env.example` documents `VITE_API_URL`; local overrides go in `frontend/.env` (gitignored)

Manually verified in-browser: an unauthenticated visit to `/meus-pedidos` redirects to `/login` with no CORS/CSRF console errors (only the expected `401` from the initial `/me/` check); the catalog grid, search/filter/ordering/pagination sync to the URL and survive browser back/forward, and the product detail page renders variações with out-of-stock sizes visibly marked.

Not yet done: no protected views beyond the `Meus Pedidos` placeholder consume real API data yet; `Header` is intentionally minimal and will be redesigned; checkout (`/checkout`, order creation) is not started — the cart only holds frontend/`localStorage` state until then.

## Development Status

- Backend: 100% complete
  - Phase 1 (Backend MVP): Complete
  - Phase 2 (REST API): Complete
  - Phase 3 (JWT Auth): Complete
- Phase 4 (React Frontend): In progress
  - Done: Axios client with CSRF header injection and single-flight refresh-on-401 interceptor; `AuthContext` (`login`/`register`/`logout`/session hydration via `/api/me/`); `PrivateRoute` guard (preserves attempted route via `state.from`); backend `/api/me/` endpoint; real `/login` and `/registro` forms (`react-hook-form` + `zod`, shared `applyApiErrors` helper — the pattern for all future forms); minimal `Header` with login/logout and a cart badge; product catalog (`Catalogo.jsx` at `/`, filters/search/ordering/pagination synced to the URL) and product detail page (`ProdutoDetalhe.jsx` at `/produtos/:id`), backed by `src/api/produtos.js`; frontend-only shopping cart (`CartContext.jsx`, `localStorage`-backed) with size/quantity selection wired up on the product page and a `/carrinho` page (public) to review/edit/remove lines
  - Remaining: full styled header, checkout flow (`/checkout`, order creation from the cart), order history view
- Phase 5 (Deploy + PostgreSQL): Planned

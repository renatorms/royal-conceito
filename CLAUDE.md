# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Royal Conceito — an e-commerce backend for a clothing store, built with Django 6 + Django REST Framework. Brazilian Portuguese is used for model/field names and UI. The frontend (React/Vite) is planned but not yet implemented.

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

- JWT via `djangorestframework-simplejwt`
- Default permission: `IsAuthenticated` (all endpoints require token)
- `produtos` ViewSets (Categoria, Marca, Produto, Variacao) use `IsAdminOrReadOnly` (`produtos/permissions.py`) — reads are public, writes require `request.user.is_staff`
- `PedidoViewSet` uses `IsAuthenticated` + `IsDonorOrStaff` (`pedidos/permissions.py`) and filters `get_queryset()` so non-staff users only see their own orders (staff see all); `perform_create()` auto-assigns `usuario` from `request.user`, so clients never submit it
- `EnderecoViewSet` uses `IsAuthenticated` + `IsDonorOrStaff`, filters `get_queryset()` by `usuario=request.user` (staff see all), and `perform_create()` forces `usuario=request.user` — closes an IDOR that let any authenticated user read/edit/delete another user's address
- `ItemPedidoViewSet` uses `IsAuthenticated` + `IsItemDonorOrStaff` (`pedidos/permissions.py`), filters `get_queryset()` by `pedido__usuario=request.user` (staff see all); `perform_create()` raises `PermissionDenied` (403) if a non-staff user targets a `Pedido` they don't own, and always sets `preco_unitario` server-side from `variacao.produto.preco` — the field is `read_only` on `ItemPedidoSerializer`, so clients can't forge a price or attach items to someone else's order
- `/api/registro/` uses `AllowAny`
- Token endpoints: `POST /api/token/` (obtain, throttled), `POST /api/token/refresh/` (refresh)

### Rate Limiting

- `DEFAULT_THROTTLE_CLASSES` = `ScopedRateThrottle`; only views with a `throttle_scope` attribute are throttled, so the rest of the API is unaffected
- `/api/token/` (`core/views.py::ThrottledTokenObtainPairView`, `throttle_scope = "login"`) and `/api/registro/` (`throttle_scope = "registro"`) are limited to 5 requests/min per client via `DEFAULT_THROTTLE_RATES` in `core/settings.py`

### Environment Variables

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` are loaded via `python-decouple` (`core/settings.py`) instead of being hardcoded
- Local values live in `backend/.env` (gitignored); `backend/.env.example` documents the expected variables
- `CORS_ALLOW_ALL_ORIGINS` is tied to `DEBUG` — all origins allowed only in dev; in production only origins listed in `CORS_ALLOWED_ORIGINS` are accepted

### Query Optimization

`ProdutoViewSet` uses `select_related("marca", "categoria").prefetch_related("variacoes")` to avoid N+1 queries. Supports `filterset_fields`, `search_fields` (nome, marca__nome), and `ordering_fields` (nome, preco).

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
| `/api/token/` | core | JWT obtain |
| `/api/token/refresh/` | core | JWT refresh |

## DRF Configuration

- Pagination: `PageNumberPagination`, 10 items per page
- Filter backends: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Auth: `JWTAuthentication`
- Throttling: `ScopedRateThrottle`, applied only to `/api/token/` and `/api/registro/` (5/min each)
- CORS: all origins allowed only when `DEBUG=True`; restricted to `CORS_ALLOWED_ORIGINS` in production

## Development Status

- Backend: 100% complete
  - Phase 1 (Backend MVP): Complete
  - Phase 2 (REST API): Complete
  - Phase 3 (JWT Auth): Complete
- Phase 4 (React Frontend): Planned
- Phase 5 (Deploy + PostgreSQL): Planned

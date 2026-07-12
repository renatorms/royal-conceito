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
- **ItemPedido** → references **Variacao** (PROTECT — can't delete sold variants)
- **Variacao** has `unique_together = ["produto", "tamanho"]`

### Business Logic via Signals

`pedidos/signals.py` contains three `post_save`/`post_delete` signals registered in `pedidos/apps.py`:

1. **diminui_estoque** — On ItemPedido creation: validates stock availability, decrements Variacao.estoque. Raises `ValueError` on insufficient stock.
2. **atualiza_total_pedido** — On ItemPedido save: recalculates Pedido.total as sum of (quantidade × preco_unitario).
3. **atualiza_total_ao_deletar** — On ItemPedido delete: recalculates Pedido.total.

### Authentication

- JWT via `djangorestframework-simplejwt`
- Default permission: `IsAuthenticated` (all endpoints require token)
- `produtos` ViewSets (Categoria, Marca, Produto, Variacao) use `IsAuthenticatedOrReadOnly` — reads are public, writes require auth
- `PedidoViewSet` uses `IsAuthenticated` + `IsDonorOrStaff` (`pedidos/permissions.py`) and filters `get_queryset()` so non-staff users only see their own orders (staff see all)
- `/api/registro/` uses `AllowAny`
- Token endpoints: `POST /api/token/` (obtain), `POST /api/token/refresh/` (refresh)

### Query Optimization

`ProdutoViewSet` uses `select_related("marca", "categoria").prefetch_related("variacoes")` to avoid N+1 queries. Supports `filterset_fields`, `search_fields` (nome, marca__nome), and `ordering_fields` (nome, preco).

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
- CORS: all origins allowed (dev only)

## Development Status

- Phase 1 (Backend MVP): Complete
- Phase 2 (REST API): Complete
- Phase 3 (JWT Auth): Complete
- Phase 4 (React Frontend): Planned
- Phase 5 (Deploy + PostgreSQL): Planned

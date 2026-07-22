<div align="center">

# 👑 Royal Conceito

### E-Commerce Platform for a Premium Fashion Store

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-3.16-ff1709?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Dev-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**Backend for a real e-commerce platform, built for a brick-and-mortar fashion store expanding into online sales.**

**Backend status: 100% complete and validated** — Phases 1, 2 and 3 finished.

[About](#-about) · [Features](#-features) · [Tech Stack](#-tech-stack) · [Architecture](#-architecture) · [API Endpoints](#-api-endpoints) · [Getting Started](#-getting-started) · [Roadmap](#-roadmap)

</div>

---

## 📋 About

**Royal Conceito** is a premium fashion store with 2 physical locations and 5 years in the market.

This project is the backend for their e-commerce platform — a REST API built with Django and Django REST Framework that handles product catalog, inventory management, and order processing with automated stock control.

> 🏪 **Real client, real business** — Built to solve actual needs of a fashion retail store.

---

## ✨ Current Features

### Product Management
- Full product catalog with categories, brands, and size variations
- Automated stock tracking per size (S, M, L, G, GG, etc.)
- `unique_together` constraint preventing duplicate size entries

### Order Processing
- Order creation with automatic total calculation via Django signals
- Stock validation — blocks orders when inventory is insufficient
- Automatic stock deduction on order creation
- Order status workflow: New → Confirmed → Shipped → Delivered | Cancelled
- `subtotal` persisted on `ItemPedido` (calculated on save, not computed on the fly)
- All order signals wrapped in atomic transactions to guarantee data consistency

### Authentication & Authorization
- JWT authentication via `djangorestframework-simplejwt`, delivered as **httpOnly cookies** rather than `Authorization: Bearer` headers (`/api/token/`, `/api/token/refresh/`, `/api/logout/`)
- CSRF protection enforced on every authenticated request — the JWT cookie rides automatically with the browser, so state-changing requests also require a valid `X-CSRFToken` header matching the `csrftoken` cookie
- `/api/me/` returns the current authenticated user (id, username, email, is_staff), used by the frontend to hydrate/validate the session
- `IsAuthenticated` enforced globally by default across the API
- `IsAdminOrReadOnly` on product endpoints — public reads, staff-only writes
- `Pedido.usuario` uses `PROTECT` — a user with existing orders can't be deleted
- Custom `IsDonorOrStaff` / `IsItemDonorOrStaff` permissions — non-staff users only see/manage their own orders, addresses, and order items; staff see all
- `perform_create()` auto-assigns `usuario` from the authenticated request — clients never submit it

### REST API
- Full CRUD endpoints for products, categories, brands, variations, orders, and addresses
- Nested serializers — single request returns product with all variations
- Query optimization with `select_related` and `prefetch_related`
- Filtering by category, brand, price range
- Search by product name and brand
- Ordering support
- Pagination built-in (10 items per page)
- Browsable API interface for testing

### Admin Dashboard
- Django Admin customized with inline editing for product variations
- Bulk stock updates directly from the list view
- Filters by category, brand, and size
- Search by product name or brand

---

## 🛠 Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Core language |
| Django | 6.0 | Web framework & ORM |
| Django REST Framework | 3.16.1 | RESTful API |
| django-filter | 25.2 | Query filtering |
| djangorestframework-simplejwt | latest | JWT authentication |
| SQLite | 3.x | Development database |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 19.2.7 | UI library |
| Vite | 8.1.1 | Build tool & dev server |
| Tailwind CSS | 4.3.3 | Styling |
| shadcn/ui | 4.13.1 | UI component primitives |
| axios | 1.18.1 | HTTP client |
| react-hook-form | 7.82.0 | Form state & validation |
| zod | 4.4.3 | Schema validation |
| react-router-dom | 7.18.1 | Client-side routing |

**Planned:** PostgreSQL (production)

---

## 🏗 Architecture

**Monolith Modular** — justified by project size (~7 models), single developer, and sufficient performance (~5000 req/sec supported vs ~20 req/sec needed).

```
sistema_loja/
├── backend/
│   ├── core/                # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py          # Root URLs (admin + API includes)
│   │   └── wsgi.py
│   │
│   ├── produtos/            # Product catalog app
│   │   ├── models.py        # Categoria, Marca, Produto, Variacao
│   │   ├── serializers.py   # 4 serializers (with nested + virtual fields)
│   │   ├── views.py         # 4 ModelViewSets
│   │   ├── urls.py          # DefaultRouter
│   │   └── admin.py         # Customized admin with inlines
│   │
│   ├── pedidos/             # Orders app
│   │   ├── models.py        # Pedido, ItemPedido, Endereco
│   │   ├── serializers.py   # 3 serializers (nested + SerializerMethodField)
│   │   ├── views.py         # 3 ModelViewSets
│   │   ├── urls.py          # DefaultRouter
│   │   ├── signals.py       # Stock validation, auto-calculations
│   │   └── admin.py         # Order management
│   │
│   ├── manage.py
│   ├── db.sqlite3
│   └── requirements.txt
│
└── frontend/                # React + Vite SPA
    ├── src/
    │   ├── pages/            # Route-level pages (Login, Registro, ...)
    │   ├── components/       # Header, PrivateRoute, ui/ (shadcn primitives)
    │   ├── contexts/         # AuthContext (session state, login/register/logout)
    │   ├── lib/              # axios instance, apiErrors helper, utils
    │   ├── schemas/          # zod schemas per form (loginSchema, registroSchema)
    │   ├── assets/
    │   ├── App.jsx           # Routes + AuthProvider + BrowserRouter
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

### Data Flow

```
HTTP Request → DRF Router → ViewSet → Serializer → Model/ORM → Signal → Database
                                                                           ↓
HTTP Response ← JSON ← Serializer ← QuerySet ←────────────────────────────┘
```

---

## 📡 API Endpoints

**Base URL:** `http://localhost:8000/api/`

### Products (Implemented ✅)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/produtos/` | List all products (paginated, with nested variations) |
| `GET` | `/api/produtos/{id}/` | Product details |
| `POST` | `/api/produtos/` | Create product |
| `PUT/PATCH` | `/api/produtos/{id}/` | Update product |
| `DELETE` | `/api/produtos/{id}/` | Delete product |
| `GET` | `/api/categorias/` | List categories |
| `GET` | `/api/marcas/` | List brands |
| `GET` | `/api/variacoes/` | List all variations |

### Orders (Implemented ✅)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/pedidos/` | List orders (with nested items) |
| `GET` | `/api/pedidos/{id}/` | Order details |
| `POST` | `/api/pedidos/` | Create order |
| `PATCH` | `/api/pedidos/{id}/` | Update order status |
| `GET` | `/api/enderecos/` | List addresses |
| `GET` | `/api/itens/` | List order items |

### Auth (Implemented ✅)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain JWT (throttled) — sets `access_token`/`refresh_token` as httpOnly cookies, no token in the JSON body |
| `POST` | `/api/token/refresh/` | Refresh JWT — reads `refresh_token` cookie, re-sets rotated cookies |
| `POST` | `/api/logout/` | Clears the JWT cookies (requires auth) |
| `POST` | `/api/registro/` | User registration (throttled) |
| `GET` | `/api/me/` | Current authenticated user (id, username, email, is_staff) |

### Query Parameters
```
?categoria=1        Filter by category
?marca=2            Filter by brand
?search=lacoste     Search by name or brand
?ordering=preco     Order by price (use -preco for descending)
```

### Example Response — `GET /api/produtos/`

```json
{
  "count": 16,
  "next": "http://127.0.0.1:8000/api/produtos/?page=2",
  "results": [
    {
      "id": 5,
      "nome": "CONJUNTO LACOSTE 2026",
      "preco": "179.99",
      "marca": 9,
      "marca_nome": "Lacoste",
      "categoria": 10,
      "categoria_nome": "Conjuntos Grifes",
      "variacoes": [
        {"id": 31, "tamanho": "S", "estoque": 10},
        {"id": 32, "tamanho": "M", "estoque": 10},
        {"id": 33, "tamanho": "L", "estoque": 10}
      ]
    }
  ]
}
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- pip
- Node.js 24.x
- npm
- Git

### Installation

```bash
# Clone
git clone https://github.com/renatorms/royal-conceito.git
cd royal-conceito/backend

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Dependencies
pip install -r requirements.txt

# Database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run
python manage.py runserver
```

**Access:**
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/

### Frontend

```bash
cd frontend

# Dependencies
npm install

# Run dev server
npm run dev
```

**Access:**
- Frontend: http://localhost:5173/

---

## 🗺 Roadmap

### Phase 1 — Backend MVP ✅
- [x] Data models (Products + Orders)
- [x] Django signals (stock validation, automatic calculations)
- [x] Customized Django Admin
- [x] Database migrations

### Phase 2 — REST API ✅
- [x] Product serializers (nested, virtual fields)
- [x] Product ViewSets + Router
- [x] Order serializers (nested, SerializerMethodField)
- [x] Order ViewSets + Router
- [x] Endpoint testing
- [x] Filters, search and ordering

### Phase 3 — JWT Authentication ✅
- [x] djangorestframework-simplejwt installed and configured
- [x] Login/register endpoints (`/api/registro/`, `/api/token/`, `/api/token/refresh/`)
- [x] Protected endpoints (`IsAuthenticated` enforced globally by default)
- [x] `IsAuthenticatedOrReadOnly` on product endpoints
- [x] `Pedido.usuario` field with `PROTECT` to prevent deleting users with orders
- [x] Custom `IsDonorOrStaff` permission for order ownership
- [x] `perform_create()` auto-assigns `usuario` from the authenticated request
- [x] `subtotal` persisted on `ItemPedido`
- [x] Atomic transactions on all order signals

### Phase 4 — Frontend (React) — In Progress
- [x] Vite + React + Tailwind + shadcn/ui setup
- [x] Project folder structure (`pages/`, `contexts/`, `lib/`, `schemas/`, `components/`)
- [x] Authentication foundation — `AuthContext`, `PrivateRoute`, axios instance with CSRF header + refresh-on-401 interceptor
- [x] Functional Login and Registro pages (`react-hook-form` + `zod`)
- [ ] Product catalog UI
- [ ] Shopping cart
- [ ] Checkout flow
- [ ] Customer order history / account area
- [ ] Responsive design (mobile-first)

### Phase 5 — Deploy
- [ ] SQLite → PostgreSQL migration
- [ ] Backend deploy (Railway/Render)
- [ ] Frontend deploy (Vercel)
- [ ] Domain + SSL

---

## 👤 Developer

| Name | Role | GitHub |
|---|---|---|
| **Renato Ramos Machado** | Fullstack Developer | [@renatorms](https://github.com/renatorms) |

Computer Engineering Student — UFSM (7th semester)

---

## 📄 License

Proprietary software developed for **Royal Conceito**. All rights reserved.

---

<div align="center">

**Built with ❤️ for Royal Conceito**

⭐ Star this repo if you find it interesting!

</div>

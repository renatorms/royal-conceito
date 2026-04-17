<div align="center">

# 👑 Royal Conceito

### E-Commerce Platform for a Premium Fashion Store

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-3.16-ff1709?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Dev-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**Backend for a real e-commerce platform, built for a brick-and-mortar fashion store expanding into online sales.**

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

### REST API
- Full CRUD endpoints for products, categories, brands, and variations
- Nested serializers — single request returns product with all variations
- Query optimization with `select_related` and `prefetch_related`
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
| SQLite | 3.x | Development database |

**Planned:** PostgreSQL (production), React + Vite (frontend), JWT authentication

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
└── frontend/                # React (planned)
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
| `GET` | `/api/enderecos/` | List addresses |
| `GET` | `/api/itens/` | List order items |

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

---

## 🗺 Roadmap

### Phase 1 — Backend MVP ✅
- [x] Data models (Products + Orders)
- [x] Django signals (stock validation, automatic calculations)
- [x] Customized Django Admin
- [x] Database migrations

### Phase 2 — REST API (In Progress)
- [x] Product serializers (nested, virtual fields)
- [x] Product ViewSets + Router
- [x] Order serializers (nested, SerializerMethodField)
- [x] Order ViewSets + Router
- [ ] Endpoint testing with Postman
- [ ] Filters and search

### Phase 3 — JWT Authentication
- [ ] djangorestframework-simplejwt setup
- [ ] Login/register endpoints
- [ ] Protected endpoints

### Phase 4 — Frontend (React)
- [ ] Vite + React setup
- [ ] Product catalog UI
- [ ] Shopping cart
- [ ] Checkout flow
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
| **Renato Ramos Machado** | Backend Developer | [@renatorms](https://github.com/renatorms) |

Computer Engineering Student — UFSM (7th semester)

---

## 📄 License

Proprietary software developed for **Royal Conceito**. All rights reserved.

---

<div align="center">

**Built with ❤️ for Royal Conceito**

⭐ Star this repo if you find it interesting!

</div>

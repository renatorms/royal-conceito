<div align="center">

# 👑 Royal Conceito

### Full-Stack E-Commerce Platform for a Fashion Retail Store

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

**A production-ready e-commerce platform built for a real brick-and-mortar fashion store, bridging the gap between physical retail and online sales.**

[Features](#-features) · [Tech Stack](#-tech-stack) · [Architecture](#-architecture) · [Getting Started](#-getting-started) · [System Flows](#-system-flows) · [API Endpoints](#-api-endpoints) · [Roadmap](#-roadmap)

</div>

---

## 📋 About

**Royal Conceito** is a full-stack e-commerce platform developed for a physical fashion retail store expanding into online sales. The project delivers a complete digital storefront — from product browsing to automated payment processing — with a custom admin dashboard for the store owner to manage products, inventory, and orders in real time.

Built with a modern decoupled architecture (Django REST API + React SPA), the platform integrates a payment gateway for seamless checkout with PIX, credit card, and boleto support.

> 🏪 **Real client, real business** — Not a tutorial project. Built to solve actual needs of a fashion retail store.

---

## ✨ Features

### 🛍️ Storefront (Customer-Facing)

- **Dynamic Home Page** — Header with logo, category navigation, search bar, and cart counter; product grid with the latest 20 items; footer with social links and WhatsApp contact
- **Product Catalog** — Filterable grid by category (dynamic fetch), search with debounce to optimize API calls
- **Product Detail Page** — Image gallery with click-to-swap, size selector (required), real-time stock validation, "Out of Stock" state with disabled button
- **Smart Shopping Cart** — `localStorage` persistence for visitors, API sync for logged-in users; real-time quantity adjustment and price calculation
- **Single-Page Checkout** — Four-section flow: Identification → Address (auto-fill via ViaCEP) → Order Summary → Payment; atomic stock validation before order creation
- **Integrated Payment** — Checkout with support for PIX, credit card, and boleto via payment gateway (Mercado Pago or Stripe — TBD)
- **User Authentication** — JWT-based login/registration, password recovery with time-limited tokens, session management
- **Order Confirmation** — Success page with order number, payment status, and summary
- **My Account (SPA)** — Order history with filters, order detail view, editable profile — all without page reloads
- **Institutional Pages** — About, Contact (WhatsApp CTA), Terms of Service, Privacy Policy

### 🏢 Admin Dashboard (SPA)

- **Overview Dashboard** — Cards showing new orders, monthly revenue, low-stock alerts (< 5 units); latest 10 orders table
- **Product Management** — Full CRUD with JS validation; drag-and-drop image upload (1–5 images) with reordering; per-size stock control (P, M, G, GG); active/inactive toggle; soft delete
- **Category Management** — Simple CRUD (name + description)
- **Order Management** — Filterable table by status/date/customer; color-coded status badges; full order detail with customer info, products, address, and WhatsApp button; editable shipping cost; status workflow: `New → Payment Confirmed → Shipped → Delivered | Cancelled`; tracking code field; internal notes; change history timeline
- **Inventory Control** — Automatic stock deduction on order (atomic transaction with rollback); automatic restoration on cancellation; manual adjustment with full audit log (`admin_id`, `timestamp`, `product_id`, `size`, `before`, `after`)
- **Store Settings** — Store name, contact info, WhatsApp number, logo upload, social media links

### 🔔 Integrations

- **Payment Gateway** — Automated payment processing (PIX, credit card, boleto) with webhook-based status updates
- **WhatsApp** — Direct `wa.me/` links for customer support and shipping coordination
- **Email Notifications** — Order confirmation, payment receipt, shipping updates, and password recovery
- **ViaCEP** — Automatic address lookup from ZIP code during checkout

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.12+** | Core language |
| **Django 5.x** | Web framework & ORM |
| **Django REST Framework** | RESTful API layer |
| **PostgreSQL** | Relational database |
| **Simple JWT** | Token-based authentication |
| **Pillow** | Image processing |
| **Mercado Pago SDK / Stripe** | Payment gateway integration (TBD) |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | UI library |
| **Vite** | Build tool & dev server |
| **React Router** | Client-side routing & SPA navigation |
| **Axios** | HTTP client for API communication |
| **Tailwind CSS** | Utility-first styling |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Render** | Backend hosting (Django + PostgreSQL) |
| **Vercel** | Frontend hosting (React SPA) |
| **GitHub Actions** | CI/CD pipeline |

---

## 🏗 Architecture

```
royal-conceito/
│
├── backend/
│   ├── config/                  # Django project configuration
│   │   ├── settings/
│   │   │   ├── base.py          # Shared settings
│   │   │   ├── dev.py           # Development overrides
│   │   │   └── prod.py          # Production overrides
│   │   ├── urls.py              # Root URL configuration
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── products/            # Product catalog, categories, images
│   │   ├── cart/                # Shopping cart logic & sync
│   │   ├── orders/              # Order creation, status workflow, history
│   │   ├── payments/            # Gateway integration & webhooks
│   │   ├── users/               # Auth, registration, password recovery
│   │   ├── inventory/           # Stock management & audit logs
│   │   └── store/               # Store settings & configurations
│   │
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Route-level page components
│   │   │   ├── Home/
│   │   │   ├── Catalog/
│   │   │   ├── ProductDetail/
│   │   │   ├── Cart/
│   │   │   ├── Checkout/
│   │   │   ├── Account/
│   │   │   └── Admin/
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API client (Axios instances)
│   │   ├── context/             # Auth, Cart providers
│   │   └── utils/               # Helpers (masks, formatters, validators)
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── PROJETO.md
└── README.md
```

---

## 🔄 System Flows

### Purchase Flow (Happy Path)

```
Customer                       Frontend                        Backend                    Gateway
   │                              │                               │                          │
   ├─ Browse catalog ────────────►│                               │                          │
   │                              ├─ GET /products/ ─────────────►│                          │
   │                              │◄── Product list ──────────────┤                          │
   ├─ Add to cart ───────────────►│── localStorage / POST /cart/ ─►                          │
   ├─ Checkout ──────────────────►│                               │                          │
   │                              ├─ POST /orders/ ──────────────►│                          │
   │                              │                               ├─ Validate stock          │
   │                              │                               ├─ Create order (atomic)   │
   │                              │                               ├─ Deduct stock            │
   │                              │                               ├─ Create payment ────────►│
   │                              │◄── Payment URL / Form ────────┤◄── Payment session ──────┤
   ├─ Complete payment ──────────►│────────────────────────────────│─────────────────────────►│
   │                              │                               │◄── Webhook: paid ────────┤
   │                              │                               ├─ Update order status     │
   │                              │                               ├─ Send confirmation email │
   │◄── Order confirmed ─────────┤◄── Success page ──────────────┤                          │
```

### Order Status Lifecycle

```
  ┌───────┐    ┌───────────────────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐
  │  New  │───►│ Payment Confirmed │───►│ Processing│───►│ Shipped │───►│ Delivered │
  └───────┘    └───────────────────┘    └───────────┘    └─────────┘    └───────────┘
      │                 │                      │
      └─────────────────┴──────────────────────┘
                        │
                  ┌─────▼─────┐
                  │ Cancelled │  ← Stock restored + refund initiated
                  └───────────┘
```

---

## 📡 API Endpoints

Documentation available at `/api/docs/` (Swagger UI) when running the backend.

### Products
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products/` | List products (filters & search) |
| `GET` | `/api/products/:id/` | Product details with images & stock |
| `GET` | `/api/categories/` | List all categories |

### Cart
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cart/` | Get user's cart |
| `POST` | `/api/cart/items/` | Add item to cart |
| `PATCH` | `/api/cart/items/:id/` | Update quantity |
| `DELETE` | `/api/cart/items/:id/` | Remove item |

### Orders & Payments
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders/` | Create order (with stock validation) |
| `GET` | `/api/orders/` | List user's orders |
| `GET` | `/api/orders/:id/` | Order details + payment status |
| `POST` | `/api/payments/create/` | Initialize payment session |
| `POST` | `/api/payments/webhook/` | Gateway webhook (status updates) |

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | User registration |
| `POST` | `/api/auth/login/` | Login (returns JWT) |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT token |
| `POST` | `/api/auth/password-reset/` | Request password reset |
| `POST` | `/api/auth/password-reset/confirm/` | Confirm reset with token |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/dashboard/` | Dashboard metrics |
| `POST` | `/api/admin/products/` | Create product |
| `PUT` | `/api/admin/products/:id/` | Update product |
| `DELETE` | `/api/admin/products/:id/` | Soft delete product |
| `PATCH` | `/api/admin/orders/:id/status/` | Update order status |
| `PATCH` | `/api/admin/orders/:id/shipping/` | Add tracking code & shipping cost |
| `GET` | `/api/admin/inventory/logs/` | Stock change audit log |

---

## 🗺 Roadmap

### Phase 1 — Foundation ✅
- [x] Project structure & initial setup
- [x] Product data modeling

### Phase 2 — Backend Core (API)
- [ ] Django project config (dev/prod split settings)
- [ ] Product & Category models + CRUD endpoints
- [ ] User authentication (JWT + password recovery flow)
- [ ] Shopping cart API (sync for logged-in users)
- [ ] Order creation with atomic stock management
- [ ] Payment gateway integration (webhooks + status sync)
- [ ] Admin endpoints (dashboard metrics, order workflow)
- [ ] Email notifications (order, payment, shipping)
- [ ] Inventory audit logging system

### Phase 3 — Frontend (React + Vite)
- [ ] Home page with dynamic product grid
- [ ] Product catalog with filters & debounced search
- [ ] Product detail page (gallery, size selector, stock check)
- [ ] Shopping cart (localStorage + API sync)
- [ ] Checkout flow with integrated payment
- [ ] Auth pages (login, register, password recovery)
- [ ] My Account area (orders, payment history, profile)
- [ ] Admin Dashboard SPA
- [ ] Responsive mobile-first design

### Phase 4 — Deploy & Polish
- [ ] Backend on Render + PostgreSQL
- [ ] Frontend on Vercel
- [ ] Environment variables & secrets
- [ ] Webhook configuration (payment gateway → backend)
- [ ] Performance optimization & testing

### Phase 5 — Future Enhancements (v2.0)
- [ ] Abandoned cart email recovery
- [ ] "Notify me when available" for out-of-stock products
- [ ] Product reviews & ratings
- [ ] Discount coupons & promotions system
- [ ] Advanced analytics dashboard
- [ ] httpOnly cookie authentication (security upgrade)

---

## 👥 Team

| | Name | GitHub | Role |
|---|---|---|---|
| 👤 | **Renato Ramos Machado** | [@renatorms](https://github.com/renatorms) | Full-Stack Developer |
| 👤 | *To be added* | — | Full-Stack Developer |

---

## 📄 License

This project is proprietary software developed for **Royal Conceito**. All rights reserved.

---

<div align="center">

**Built with ❤️ for Royal Conceito**

⭐ Star this repo if you find it interesting!

</div>

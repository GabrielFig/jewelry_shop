# E-Commerce Platform — Jewelry Shop

A production-ready e-commerce backend built with **Python + FastAPI**, following **Clean Architecture**, **Domain-Driven Design (DDD)**, and several classic design patterns. The default configuration is a jewelry shop, but the architecture is intentionally generic — see *Adapting to Other Domains* below to repurpose it in minutes.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Patterns](#design-patterns)
3. [Quick Start with Docker](#quick-start-with-docker)
4. [Local Development Setup](#local-development-setup)
5. [API Reference](#api-reference)
6. [Adapting to Other E-Commerce Domains](#adapting-to-other-e-commerce-domains)
7. [Environment Variables](#environment-variables)
8. [Running Tests](#running-tests)
9. [Project Structure](#project-structure)

---

## Architecture Overview

```
HTTP Request
     │
     ▼
┌─────────────────────────────┐
│  Entrypoints (FastAPI)       │   app/entrypoints/
│  Routers: products, orders,  │   → validates HTTP input, calls service layer
│  customers, inventory …      │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Service Layer               │   app/service_layer/services.py
│  Use cases / Application     │   → orchestrates domain objects + UoW
│  services                    │   → publishes domain events
└────────────┬────────────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
┌──────────┐   ┌──────────────────────────┐
│  Domain   │   │  Message Bus              │   app/message_bus.py
│  Models   │   │  Dispatches domain events │
│  Services │   │  to registered handlers   │
│  Events   │   └──────────────────────────┘
└──────────┘
     │
     ▼
┌─────────────────────────────┐
│  Adapters                    │   app/adapters/
│  Repositories (SQLAlchemy)   │   → translate between domain ↔ DB
│  ORM Models                  │
└────────────┬────────────────┘
             │
             ▼
       PostgreSQL / SQLite
```

### Layers

| Layer | Folder | Depends on |
|---|---|---|
| **Domain** | `app/domain/` | Nothing (pure Python) |
| **Service Layer** | `app/service_layer/` | Domain |
| **Adapters** | `app/adapters/` | Domain, SQLAlchemy |
| **Entrypoints** | `app/entrypoints/` | Service layer, Pydantic |
| **Infrastructure** | `app/unit_of_work.py`, `app/message_bus.py` | Adapters, Service layer |

The domain layer has **zero** imports from FastAPI, SQLAlchemy, or any external library — it is fully unit-testable in memory.

---

## Design Patterns

### 1. Repository Pattern
Each aggregate root has an abstract repository interface and two concrete implementations:

```
AbstractXxxRepository    ← interface (service layer depends only on this)
InMemoryXxxRepository    ← used in unit tests, no DB needed
SqlAlchemyXxxRepository  ← production implementation
```

Adding a new entity: define its abstract + in-memory + SQLAlchemy repositories in `app/adapters/repository.py`, then wire it into the UoW.

### 2. Unit of Work Pattern
`AbstractUnitOfWork` groups all repositories into a single transaction boundary. The caller controls commit / rollback:

```python
with SqlAlchemyUnitOfWork() as uow:
    product = services.get_product("RING-001", uow)
    product.update_price(Money(Decimal("499"), "USD"))
    uow.products.update(product)
    uow.commit()
```

Tests inject `InMemoryUnitOfWork` — no database required.

### 3. Strategy Pattern (Payments)
`Order.pay()` accepts any `AbstractPaymentStrategy`:

```python
class AbstractPaymentStrategy(ABC):
    @abstractmethod
    def process(self, order: Order) -> bool: ...
```

Built-in strategies:

| Strategy key | Class | When to use |
|---|---|---|
| `"mock"` | `MockPaymentStrategy` | Development / tests |
| `"credit_card"` | `CreditCardPaymentStrategy` | Placeholder for Stripe / Braintree |

Adding a new payment method (e.g. PayPal):

```python
# app/domain/strategies.py
class PayPalStrategy(AbstractPaymentStrategy):
    def __init__(self, client_id: str, secret: str):
        self.client_id = client_id
        self.secret = secret

    def process(self, order: Order) -> bool:
        # call PayPal SDK here
        return True

PAYMENT_STRATEGIES["paypal"] = PayPalStrategy
```

Then call via the API:
```json
POST /orders/{id}/pay
{ "payment_method": "paypal", "extra_params": {"client_id": "...", "secret": "..."} }
```

### 4. Domain-Driven Design (DDD)
- **Domain models** (`app/domain/models.py`) encapsulate business rules and emit domain events.
- **Domain services** (`app/domain/services.py`) contain pure logic spanning multiple aggregates (e.g., the allocation algorithm).
- **Value objects** (`app/domain/value_objects.py`): `Money`, `Address` — immutable, equality by value.
- **Domain events** (`app/domain/events.py`): lightweight dataclasses published after state changes.

### 5. Observer / Message Bus
Domain events are dispatched to the bus after each committed transaction. Handlers produce side effects without coupling to the domain:

```
OrderPaid event  →  on_order_paid()  →  writes to SENT_NOTIFICATIONS
                                      →  (add) send email, push to Kafka, etc.
```

Register a new handler:
```python
# app/message_bus.py
HANDLERS[events.OrderPaid].append(my_email_handler)
```

---

## Quick Start with Docker

**Prerequisites:** Docker >= 24, Docker Compose >= 2

### Production mode

```bash
cp .env.example .env     # adjust passwords if desired
docker compose up --build -d
```

- API: **http://localhost:8000**
- Interactive docs: **http://localhost:8000/docs**

### Development mode (hot-reload + seed data)

```bash
docker compose --profile dev up app-dev --build
```

Source files are volume-mounted — edits reflect instantly without a rebuild. The dev service also runs `python init_db.py --seed` on first start to populate sample jewelry products.

---

## Local Development Setup

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd jewelry_shop

# 2. Create a virtual environment
python -m venv .env && source .env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the database (SQLite = no Postgres needed)
export DATABASE_URL="sqlite:///./dev.db"

# 5. Create tables and insert sample data
python init_db.py --seed

# 6. Start with live reload
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive API explorer.

---

## API Reference

All endpoints return JSON. Errors return `{"detail": "message"}`.

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/notifications` | Domain event log |

---

### Categories

| Method | Path | Description |
|---|---|---|
| `POST` | `/categories` | Create a category |
| `GET` | `/categories` | List all categories |
| `GET` | `/categories/{id}` | Get a category |

```bash
curl -X POST http://localhost:8000/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Rings", "description": "Finger rings of all styles"}'
```

---

### Products

| Method | Path | Description |
|---|---|---|
| `POST` | `/products` | Create a product |
| `GET` | `/products` | List (filter: `?category_id=&active_only=true`) |
| `GET` | `/products/{sku}` | Get a product |
| `PATCH` | `/products/{sku}/price` | Update price |
| `DELETE` | `/products/{sku}` | Deactivate |

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "RING-GOLD-001",
    "name": "18k Gold Solitaire Ring",
    "description": "Classic solitaire, 0.5ct diamond",
    "price_amount": 899.99,
    "price_currency": "USD",
    "category_id": "<uuid>",
    "attributes": {
      "material": "18k gold",
      "gemstone": "diamond",
      "gemstone_weight_ct": 0.5,
      "ring_size": "7",
      "weight_g": 4.2
    }
  }'
```

---

### Customers

| Method | Path | Description |
|---|---|---|
| `POST` | `/customers` | Register a customer |
| `GET` | `/customers` | List all customers |
| `GET` | `/customers/{id}` | Get a customer |

```bash
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "name": "Alice"}'
```

---

### Orders

| Method | Path | Description |
|---|---|---|
| `POST` | `/orders` | Create an order |
| `GET` | `/orders/{order_id}` | Get an order |
| `GET` | `/orders/customer/{customer_id}` | List customer orders |
| `POST` | `/orders/{order_id}/items` | Add an item |
| `POST` | `/orders/{order_id}/confirm` | Confirm the order |
| `POST` | `/orders/{order_id}/pay` | Pay |
| `POST` | `/orders/{order_id}/ship` | Mark as shipped |
| `POST` | `/orders/{order_id}/cancel` | Cancel |

**Status flow:**
```
PENDING → CONFIRMED → PAID → SHIPPED → DELIVERED
                           ↘ CANCELLED (any state before SHIPPED)
```

**Full order example:**
```bash
# 1. Create
ORDER_ID=$(curl -s -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "<uuid>"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 2. Add item
curl -X POST "http://localhost:8000/orders/$ORDER_ID/items" \
  -H "Content-Type: application/json" \
  -d '{"sku": "RING-GOLD-001", "quantity": 1}'

# 3. Confirm
curl -X POST "http://localhost:8000/orders/$ORDER_ID/confirm"

# 4. Pay (mock in dev)
curl -X POST "http://localhost:8000/orders/$ORDER_ID/pay" \
  -H "Content-Type: application/json" \
  -d '{"payment_method": "mock"}'

# 5. Ship
curl -X POST "http://localhost:8000/orders/$ORDER_ID/ship"
```

---

### Inventory

| Method | Path | Description |
|---|---|---|
| `POST` | `/inventory/batches` | Add a stock batch |
| `GET` | `/inventory/batches` | List batches |
| `POST` | `/inventory/allocate` | Allocate stock to an order |

```bash
# Add 20 units of stock
curl -X POST http://localhost:8000/inventory/batches \
  -H "Content-Type: application/json" \
  -d '{"reference": "BATCH-001", "sku": "RING-GOLD-001", "quantity": 20}'

# Allocate 2 units
curl -X POST http://localhost:8000/inventory/allocate \
  -H "Content-Type: application/json" \
  -d '{"order_id": "order-123", "sku": "RING-GOLD-001", "quantity": 2}'
```

---

## Adapting to Other E-Commerce Domains

The platform is domain-agnostic. The only jewelry-specific code is the seed data in `init_db.py`. Here is how to repurpose the platform:

### Step 1 — Change categories

```python
# init_db.py  →  seed_data()
services.create_category("Laptops", "Portable computers", uow)
services.create_category("Phones", "Smartphones", uow)
```

### Step 2 — Use domain-specific `attributes`

The `attributes: dict` field stores any key-value pairs for a product without schema changes:

```python
# Electronics
{"brand": "Apple", "model": "MacBook Pro 16", "cpu": "M3 Pro", "ram_gb": 36}

# Clothing
{"size": "XL", "color": "forest green", "fabric": "90% cotton"}

# Food & Beverage
{"weight_kg": 0.25, "organic": True, "allergens": ["gluten"], "expiry_days": 180}
```

### Step 3 — Add a real payment strategy

```python
# app/domain/strategies.py
class StripeStrategy(AbstractPaymentStrategy):
    def __init__(self, token: str):
        self.token = token

    def process(self, order: Order) -> bool:
        import stripe, os
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        intent = stripe.PaymentIntent.create(
            amount=int(order.total.amount * 100),
            currency=order.total.currency.lower(),
            payment_method=self.token,
            confirm=True,
        )
        return intent.status == "succeeded"

PAYMENT_STRATEGIES["stripe"] = StripeStrategy
```

### Step 4 — Add domain-specific event handlers

```python
# app/service_layer/handlers.py
def on_order_paid(event: events.OrderPaid) -> None:
    send_receipt_email(event.order_id, event.amount)
    update_analytics_dashboard(event.order_id)
```

No other files need to change.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/ecommerce` | DB connection string |
| `POSTGRES_PASSWORD` | `postgres` | Postgres password (docker compose) |
| `POSTGRES_DB` | `ecommerce` | Database name (docker compose) |
| `DB_PORT` | `5432` | Host port for Postgres |
| `APP_PORT` | `8000` | Host port for the API |
| `LOG_LEVEL` | `info` | Uvicorn log level |

---

## Running Tests

```bash
# Domain + service layer unit tests (no DB required)
DATABASE_URL=sqlite:///./test.db pytest tests/domain tests/service_layer -v

# With coverage
DATABASE_URL=sqlite:///./test.db pytest tests/domain tests/service_layer \
  --cov=app --cov-report=term-missing
```

All unit tests use `InMemoryUnitOfWork` — no database process is required.

---

## Project Structure

```
jewelry_shop/
├── app/
│   ├── domain/
│   │   ├── models.py          # Entities: Batch, Product, Customer, Order …
│   │   ├── value_objects.py   # Money, Address (immutable)
│   │   ├── events.py          # Domain events (pure dataclasses)
│   │   ├── services.py        # Pure domain logic (allocation algorithm)
│   │   └── strategies.py      # Concrete payment strategies + factory
│   ├── adapters/
│   │   ├── sqlalchemy_models.py  # ORM models (infrastructure only)
│   │   └── repository.py         # Abstract + in-memory + SQLAlchemy repos
│   ├── service_layer/
│   │   ├── services.py        # Application use cases
│   │   └── handlers.py        # Domain event side-effect handlers
│   ├── entrypoints/
│   │   ├── api.py             # Root router assembly
│   │   └── routers/
│   │       ├── categories.py
│   │       ├── products.py
│   │       ├── customers.py
│   │       ├── orders.py
│   │       └── inventory.py
│   ├── unit_of_work.py        # UoW pattern (transaction boundary)
│   ├── message_bus.py         # Event dispatch
│   └── notifications.py       # In-memory notification store
├── tests/
│   ├── domain/test_services.py
│   └── service_layer/test_events.py
├── main.py                    # FastAPI entry point
├── init_db.py                 # Table creation + optional seed data
├── Dockerfile                 # Multi-stage build
├── docker-compose.yml         # Services: db, app (prod), app-dev
├── requirements.txt
├── .env.example
└── README.md
```

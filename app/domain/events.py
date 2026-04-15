"""
Domain Events — pure dataclasses with no dependencies on infrastructure.

Events are raised by domain models and collected by the service layer,
which passes them to the message bus for dispatch.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


# ─── Inventory Events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrderAllocated:
    order_id: str
    sku: str
    quantity: int
    batch_ref: str


@dataclass(frozen=True)
class OutOfStock:
    sku: str


@dataclass(frozen=True)
class BatchAdded:
    ref: str
    sku: str
    quantity: int


# ─── Catalog Events ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProductCreated:
    sku: str
    name: str
    category_id: str


@dataclass(frozen=True)
class ProductPriceChanged:
    sku: str
    old_price_amount: Decimal
    new_price_amount: Decimal
    currency: str


@dataclass(frozen=True)
class ProductDeactivated:
    sku: str


@dataclass(frozen=True)
class CategoryCreated:
    id: str
    name: str


# ─── Customer Events ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CustomerCreated:
    customer_id: str
    email: str
    name: str


# ─── Order Events ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrderCreated:
    order_id: str
    customer_id: str


@dataclass(frozen=True)
class OrderItemAdded:
    order_id: str
    sku: str
    quantity: int


@dataclass(frozen=True)
class OrderConfirmed:
    order_id: str


@dataclass(frozen=True)
class OrderPaid:
    order_id: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class OrderShipped:
    order_id: str


@dataclass(frozen=True)
class OrderCancelled:
    order_id: str

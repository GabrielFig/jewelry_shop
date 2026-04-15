"""
Application services (use cases) — orchestrate domain objects and the UoW.

Rules:
  - Services receive a UnitOfWork, call domain methods, commit, then publish events.
  - Services do NOT manage the UoW context (no `with uow:`) — that is the
    entrypoint's responsibility.
  - Services do NOT import from FastAPI, SQLAlchemy, or any infrastructure module.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.domain.models import (
    Batch,
    Category,
    Customer,
    Order,
    OrderLine,
    Product,
)
from app.domain.services import allocate as domain_allocate
from app.domain.strategies import get_payment_strategy
from app.domain.value_objects import Money
from app.domain.events import BatchAdded, OutOfStock, OrderAllocated
from app.message_bus import publish_all
from app.unit_of_work import AbstractUnitOfWork


# ─── Category services ────────────────────────────────────────────────────────

def create_category(name: str, description: str, uow: AbstractUnitOfWork) -> Category:
    existing = next((c for c in uow.categories.list() if c.name == name), None)
    if existing:
        raise ValueError(f"Category '{name}' already exists")
    category = Category(id=str(uuid.uuid4()), name=name, description=description)
    uow.categories.add(category)
    uow.commit()
    publish_all(category.events)
    return category


def list_categories(uow: AbstractUnitOfWork) -> List[Category]:
    return uow.categories.list()


def get_category(id: str, uow: AbstractUnitOfWork) -> Category:
    category = uow.categories.get(id)
    if not category:
        raise ValueError(f"Category '{id}' not found")
    return category


# ─── Product services ─────────────────────────────────────────────────────────

def create_product(
    sku: str,
    name: str,
    description: str,
    price_amount: Decimal,
    price_currency: str,
    category_id: str,
    attributes: Optional[Dict[str, Any]],
    image_url: str,
    uow: AbstractUnitOfWork,
) -> Product:
    if uow.products.get(sku):
        raise ValueError(f"Product with SKU '{sku}' already exists")
    if not uow.categories.get(category_id):
        raise ValueError(f"Category '{category_id}' does not exist")
    product = Product(
        sku=sku,
        name=name,
        description=description,
        price=Money(amount=price_amount, currency=price_currency),
        category_id=category_id,
        attributes=attributes or {},
        image_url=image_url,
    )
    uow.products.add(product)
    uow.commit()
    publish_all(product.events)
    return product


def list_products(
    uow: AbstractUnitOfWork,
    category_id: Optional[str] = None,
    active_only: bool = True,
) -> List[Product]:
    return uow.products.list(category_id=category_id, active_only=active_only)


def get_product(sku: str, uow: AbstractUnitOfWork) -> Product:
    product = uow.products.get(sku)
    if not product:
        raise ValueError(f"Product '{sku}' not found")
    return product


def update_product_price(
    sku: str, new_amount: Decimal, currency: str, uow: AbstractUnitOfWork
) -> Product:
    product = get_product(sku, uow)
    product.update_price(Money(amount=new_amount, currency=currency))
    uow.products.update(product)
    uow.commit()
    publish_all(product.events)
    return product


def deactivate_product(sku: str, uow: AbstractUnitOfWork) -> Product:
    product = get_product(sku, uow)
    product.deactivate()
    uow.products.update(product)
    uow.commit()
    publish_all(product.events)
    return product


# ─── Customer services ────────────────────────────────────────────────────────

def create_customer(email: str, name: str, uow: AbstractUnitOfWork) -> Customer:
    if uow.customers.get_by_email(email):
        raise ValueError(f"Customer with email '{email}' already exists")
    customer = Customer(id=str(uuid.uuid4()), email=email, name=name)
    uow.customers.add(customer)
    uow.commit()
    publish_all(customer.events)
    return customer


def get_customer(id: str, uow: AbstractUnitOfWork) -> Customer:
    customer = uow.customers.get(id)
    if not customer:
        raise ValueError(f"Customer '{id}' not found")
    return customer


def list_customers(uow: AbstractUnitOfWork) -> List[Customer]:
    return uow.customers.list()


# ─── Order services ───────────────────────────────────────────────────────────

def create_order(customer_id: str, uow: AbstractUnitOfWork) -> Order:
    if not uow.customers.get(customer_id):
        raise ValueError(f"Customer '{customer_id}' does not exist")
    order = Order(id=str(uuid.uuid4()), customer_id=customer_id)
    uow.orders.add(order)
    uow.commit()
    publish_all(order.events)
    return order


def add_item_to_order(
    order_id: str, sku: str, quantity: int, uow: AbstractUnitOfWork
) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    product = uow.products.get(sku)
    if not product:
        raise ValueError(f"Product '{sku}' not found")
    if not product.is_active:
        raise ValueError(f"Product '{sku}' is not available for purchase")
    order.add_item(sku=sku, quantity=quantity, unit_price=product.price)
    uow.orders.update(order)
    uow.commit()
    publish_all(order.events)
    return order


def confirm_order(order_id: str, uow: AbstractUnitOfWork) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    order.confirm()
    uow.orders.update(order)
    uow.commit()
    publish_all(order.events)
    return order


def pay_order(
    order_id: str,
    payment_method: str,
    uow: AbstractUnitOfWork,
    **payment_kwargs: Any,
) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    strategy = get_payment_strategy(payment_method, **payment_kwargs)
    order.pay(strategy)
    uow.orders.update(order)
    uow.commit()
    publish_all(order.events)
    return order


def ship_order(order_id: str, uow: AbstractUnitOfWork) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    order.ship()
    uow.orders.update(order)
    uow.commit()
    publish_all(order.events)
    return order


def cancel_order(order_id: str, uow: AbstractUnitOfWork) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    order.cancel()
    uow.orders.update(order)
    uow.commit()
    publish_all(order.events)
    return order


def get_order(order_id: str, uow: AbstractUnitOfWork) -> Order:
    order = uow.orders.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found")
    return order


def list_customer_orders(customer_id: str, uow: AbstractUnitOfWork) -> List[Order]:
    return uow.orders.list_by_customer(customer_id)


# ─── Inventory services ───────────────────────────────────────────────────────

def add_batch(
    ref: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    uow: AbstractUnitOfWork,
) -> Batch:
    if uow.batches.get(ref):
        raise ValueError(f"Batch '{ref}' already exists")
    batch = Batch(ref=ref, sku=sku, purchased_quantity=quantity, eta=eta)
    uow.batches.add(batch)
    uow.commit()
    publish_all([BatchAdded(ref=ref, sku=sku, quantity=quantity)])
    return batch


def allocate_order(
    order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork
) -> str:
    line = OrderLine(order_id=order_id, sku=sku, quantity=qty)
    batches = uow.batches.list()
    batch_ref, domain_events = domain_allocate(line, batches)
    if not batch_ref:
        uow.commit()
        publish_all(domain_events)
        raise ValueError(f"Out of stock for SKU: {sku}")
    uow.commit()
    publish_all(domain_events)
    return batch_ref

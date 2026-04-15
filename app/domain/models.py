"""
Domain Models — pure business logic with no framework or infrastructure dependencies.

Design:
  - Batch / OrderLine  → inventory allocation (original core)
  - Category           → product grouping
  - Product            → generic catalog item; `attributes` dict makes it
                         extensible for ANY e-commerce domain:
                           jewelry:     {"material": "gold", "gemstone": "diamond"}
                           electronics: {"brand": "Sony", "warranty_years": 2}
                           clothing:    {"size": "M", "color": "red"}
  - Customer           → buyer
  - Order / OrderItem  → purchase transaction

Payment is handled via the Strategy pattern (AbstractPaymentStrategy).
Concrete strategies live in app/domain/strategies.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from app.domain.value_objects import Money, Address
from app.domain.events import (
    BatchAdded,
    CategoryCreated,
    CustomerCreated,
    OrderAllocated,
    OrderCancelled,
    OrderConfirmed,
    OrderCreated,
    OrderItemAdded,
    OrderPaid,
    OrderShipped,
    OutOfStock,
    ProductCreated,
    ProductDeactivated,
    ProductPriceChanged,
)


# ─── Inventory ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrderLine:
    """Represents a single line in an allocation request."""
    order_id: str
    sku: str
    quantity: int


class Batch:
    """
    A batch of inventory for a specific SKU.
    Tracks how many units have been allocated to orders.
    """

    def __init__(
        self,
        ref: str,
        sku: str,
        purchased_quantity: int,
        eta: Optional[date] = None,
    ):
        self.ref = ref
        self.sku = sku
        self.purchased_quantity = purchased_quantity
        self.eta = eta
        self._allocations: set[OrderLine] = set()
        self.events: list = []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return NotImplemented
        return self.ref == other.ref

    def __hash__(self) -> int:
        return hash(self.ref)

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self.purchased_quantity - self.allocated_quantity


# ─── Catalog ─────────────────────────────────────────────────────────────────

class Category:
    """
    Product category. Hierarchical categorisation is possible by adding a
    parent_id field in future iterations.
    """

    def __init__(self, id: str, name: str, description: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.events: list = [CategoryCreated(id=id, name=name)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class Product:
    """
    Generic product entity.

    The `attributes` dictionary is the extensibility hook that makes this model
    reusable across e-commerce domains without changing the core schema:

        Jewelry shop   → {"material": "18k gold", "gemstone": "emerald", "weight_g": 4.5}
        Electronics    → {"brand": "Apple", "model": "AirPods Pro", "connectivity": "Bluetooth"}
        Fashion        → {"size": "L", "color": "navy", "fabric": "100% cotton"}
        Food & Drink   → {"weight_kg": 0.5, "organic": True, "allergens": ["nuts"]}
    """

    def __init__(
        self,
        sku: str,
        name: str,
        description: str,
        price: Money,
        category_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        image_url: str = "",
    ):
        self.sku = sku
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id
        self.attributes = attributes or {}
        self.image_url = image_url
        self.is_active = True
        self.events: list = [ProductCreated(sku=sku, name=name, category_id=category_id)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.sku == other.sku

    def __hash__(self) -> int:
        return hash(self.sku)

    def update_price(self, new_price: Money) -> None:
        self.events.append(
            ProductPriceChanged(
                sku=self.sku,
                old_price_amount=self.price.amount,
                new_price_amount=new_price.amount,
                currency=new_price.currency,
            )
        )
        self.price = new_price

    def deactivate(self) -> None:
        self.is_active = False
        self.events.append(ProductDeactivated(sku=self.sku))

    def activate(self) -> None:
        self.is_active = True


# ─── Customers ───────────────────────────────────────────────────────────────

class Customer:
    def __init__(self, id: str, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name
        self.addresses: List[Address] = []
        self.events: list = [CustomerCreated(customer_id=id, email=email, name=name)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def add_address(self, address: Address) -> None:
        self.addresses.append(address)


# ─── Orders ──────────────────────────────────────────────────────────────────

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


class Order:
    """
    An order aggregates order items and drives the purchase lifecycle:
    PENDING → CONFIRMED → PAID → SHIPPED → DELIVERED
                                         ↘ CANCELLED (any state before SHIPPED)
    """

    def __init__(self, id: str, customer_id: str):
        self.id = id
        self.customer_id = customer_id
        self.items: List[OrderItem] = []
        self.status = OrderStatus.PENDING
        self.events: list = [OrderCreated(order_id=id, customer_id=customer_id)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def add_item(self, sku: str, quantity: int, unit_price: Money) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Items can only be added to pending orders")
        self.items.append(OrderItem(sku=sku, quantity=quantity, unit_price=unit_price))
        self.events.append(OrderItemAdded(order_id=self.id, sku=sku, quantity=quantity))

    @property
    def total(self) -> Money:
        if not self.items:
            return Money(amount=Decimal("0"), currency="USD")
        subtotals = [item.subtotal for item in self.items]
        result = subtotals[0]
        for s in subtotals[1:]:
            result = result + s
        return result

    def confirm(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")
        if not self.items:
            raise ValueError("Cannot confirm an empty order")
        self.status = OrderStatus.CONFIRMED
        self.events.append(OrderConfirmed(order_id=self.id))

    def pay(self, payment_strategy: "AbstractPaymentStrategy") -> None:
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Only confirmed orders can be paid")
        success = payment_strategy.process(self)
        if not success:
            raise ValueError("Payment processing failed")
        self.status = OrderStatus.PAID
        total = self.total
        self.events.append(
            OrderPaid(order_id=self.id, amount=total.amount, currency=total.currency)
        )

    def ship(self) -> None:
        if self.status != OrderStatus.PAID:
            raise ValueError("Only paid orders can be shipped")
        self.status = OrderStatus.SHIPPED
        self.events.append(OrderShipped(order_id=self.id))

    def cancel(self) -> None:
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise ValueError("Cannot cancel an order that has already been shipped")
        self.status = OrderStatus.CANCELLED
        self.events.append(OrderCancelled(order_id=self.id))


# ─── Payment Strategy (abstract) ─────────────────────────────────────────────

class AbstractPaymentStrategy(ABC):
    """
    Strategy interface for payment processing.
    Swap implementations without touching the Order domain model.

    Built-in strategies:   MockPaymentStrategy, CreditCardPaymentStrategy
    Add your own by:       subclassing AbstractPaymentStrategy and implementing process()
    """

    @abstractmethod
    def process(self, order: Order) -> bool:
        """Return True on success, False on failure."""

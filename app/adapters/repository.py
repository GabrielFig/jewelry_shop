"""
Repository pattern — abstracts data access behind interfaces.

Each aggregate root has:
  - An Abstract* base class (the interface, used by the service layer)
  - An InMemory* implementation (for unit tests, no DB required)
  - A SqlAlchemy* implementation (for production / integration tests)

Adding a new aggregate:
  1. Define AbstractXxxRepository with add / get / list.
  2. Implement InMemoryXxxRepository for tests.
  3. Implement SqlAlchemyXxxRepository for production.
  4. Wire into AbstractUnitOfWork in unit_of_work.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.models import Batch, Category, Customer, Order, OrderItem, OrderStatus, Product
from app.domain.value_objects import Money
from app.adapters.sqlalchemy_models import (
    BatchModel,
    CategoryModel,
    CustomerModel,
    OrderItemModel,
    OrderModel,
    ProductModel,
)


# ─── Category ────────────────────────────────────────────────────────────────

class AbstractCategoryRepository(ABC):
    @abstractmethod
    def add(self, category: Category) -> None: ...

    @abstractmethod
    def get(self, id: str) -> Optional[Category]: ...

    @abstractmethod
    def list(self) -> List[Category]: ...


class InMemoryCategoryRepository(AbstractCategoryRepository):
    def __init__(self):
        self._store: List[Category] = []

    def add(self, category: Category) -> None:
        self._store.append(category)

    def get(self, id: str) -> Optional[Category]:
        return next((c for c in self._store if c.id == id), None)

    def list(self) -> List[Category]:
        return list(self._store)


class SqlAlchemyCategoryRepository(AbstractCategoryRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, category: Category) -> None:
        model = CategoryModel(id=category.id, name=category.name, description=category.description)
        self._session.add(model)

    def get(self, id: str) -> Optional[Category]:
        model = self._session.query(CategoryModel).filter_by(id=id).first()
        return _category_from_model(model) if model else None

    def list(self) -> List[Category]:
        return [_category_from_model(m) for m in self._session.query(CategoryModel).all()]


def _category_from_model(m: CategoryModel) -> Category:
    c = Category.__new__(Category)
    c.id = str(m.id)
    c.name = str(m.name)
    c.description = str(m.description or "")
    c.events = []
    return c


# ─── Product ─────────────────────────────────────────────────────────────────

class AbstractProductRepository(ABC):
    @abstractmethod
    def add(self, product: Product) -> None: ...

    @abstractmethod
    def get(self, sku: str) -> Optional[Product]: ...

    @abstractmethod
    def list(self, category_id: Optional[str] = None, active_only: bool = True) -> List[Product]: ...

    @abstractmethod
    def update(self, product: Product) -> None: ...


class InMemoryProductRepository(AbstractProductRepository):
    def __init__(self):
        self._store: List[Product] = []

    def add(self, product: Product) -> None:
        self._store.append(product)

    def get(self, sku: str) -> Optional[Product]:
        return next((p for p in self._store if p.sku == sku), None)

    def list(self, category_id: Optional[str] = None, active_only: bool = True) -> List[Product]:
        result = self._store
        if active_only:
            result = [p for p in result if p.is_active]
        if category_id:
            result = [p for p in result if p.category_id == category_id]
        return list(result)

    def update(self, product: Product) -> None:
        pass  # in-memory objects are already mutated in place


class SqlAlchemyProductRepository(AbstractProductRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, product: Product) -> None:
        model = ProductModel(
            sku=product.sku,
            name=product.name,
            description=product.description,
            price_amount=product.price.amount,
            price_currency=product.price.currency,
            category_id=product.category_id,
            attributes=product.attributes,
            image_url=product.image_url,
            is_active=product.is_active,
        )
        self._session.add(model)

    def get(self, sku: str) -> Optional[Product]:
        model = self._session.query(ProductModel).filter_by(sku=sku).first()
        return _product_from_model(model) if model else None

    def list(self, category_id: Optional[str] = None, active_only: bool = True) -> List[Product]:
        q = self._session.query(ProductModel)
        if active_only:
            q = q.filter_by(is_active=True)
        if category_id:
            q = q.filter_by(category_id=category_id)
        return [_product_from_model(m) for m in q.all()]

    def update(self, product: Product) -> None:
        model = self._session.query(ProductModel).filter_by(sku=product.sku).first()
        if model:
            model.name = product.name
            model.description = product.description
            model.price_amount = product.price.amount
            model.price_currency = product.price.currency
            model.category_id = product.category_id
            model.attributes = product.attributes
            model.image_url = product.image_url
            model.is_active = product.is_active


def _product_from_model(m: ProductModel) -> Product:
    p = Product.__new__(Product)
    p.sku = str(m.sku)
    p.name = str(m.name)
    p.description = str(m.description or "")
    p.price = Money(amount=Decimal(str(m.price_amount)), currency=str(m.price_currency))
    p.category_id = str(m.category_id)
    p.attributes = dict(m.attributes) if m.attributes else {}
    p.image_url = str(m.image_url or "")
    p.is_active = bool(m.is_active)
    p.events = []
    return p


# ─── Customer ────────────────────────────────────────────────────────────────

class AbstractCustomerRepository(ABC):
    @abstractmethod
    def add(self, customer: Customer) -> None: ...

    @abstractmethod
    def get(self, id: str) -> Optional[Customer]: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Customer]: ...

    @abstractmethod
    def list(self) -> List[Customer]: ...


class InMemoryCustomerRepository(AbstractCustomerRepository):
    def __init__(self):
        self._store: List[Customer] = []

    def add(self, customer: Customer) -> None:
        self._store.append(customer)

    def get(self, id: str) -> Optional[Customer]:
        return next((c for c in self._store if c.id == id), None)

    def get_by_email(self, email: str) -> Optional[Customer]:
        return next((c for c in self._store if c.email == email), None)

    def list(self) -> List[Customer]:
        return list(self._store)


class SqlAlchemyCustomerRepository(AbstractCustomerRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, customer: Customer) -> None:
        model = CustomerModel(id=customer.id, email=customer.email, name=customer.name)
        self._session.add(model)

    def get(self, id: str) -> Optional[Customer]:
        model = self._session.query(CustomerModel).filter_by(id=id).first()
        return _customer_from_model(model) if model else None

    def get_by_email(self, email: str) -> Optional[Customer]:
        model = self._session.query(CustomerModel).filter_by(email=email).first()
        return _customer_from_model(model) if model else None

    def list(self) -> List[Customer]:
        return [_customer_from_model(m) for m in self._session.query(CustomerModel).all()]


def _customer_from_model(m: CustomerModel) -> Customer:
    c = Customer.__new__(Customer)
    c.id = str(m.id)
    c.email = str(m.email)
    c.name = str(m.name)
    c.addresses = []
    c.events = []
    return c


# ─── Order ───────────────────────────────────────────────────────────────────

class AbstractOrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> None: ...

    @abstractmethod
    def get(self, id: str) -> Optional[Order]: ...

    @abstractmethod
    def list_by_customer(self, customer_id: str) -> List[Order]: ...

    @abstractmethod
    def update(self, order: Order) -> None: ...


class InMemoryOrderRepository(AbstractOrderRepository):
    def __init__(self):
        self._store: List[Order] = []

    def add(self, order: Order) -> None:
        self._store.append(order)

    def get(self, id: str) -> Optional[Order]:
        return next((o for o in self._store if o.id == id), None)

    def list_by_customer(self, customer_id: str) -> List[Order]:
        return [o for o in self._store if o.customer_id == customer_id]

    def update(self, order: Order) -> None:
        pass  # in-memory objects mutated in place


class SqlAlchemyOrderRepository(AbstractOrderRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, order: Order) -> None:
        model = OrderModel(
            id=order.id,
            customer_id=order.customer_id,
            status=order.status.value,
        )
        for item in order.items:
            model.items.append(
                OrderItemModel(
                    order_id=order.id,
                    sku=item.sku,
                    quantity=item.quantity,
                    unit_price_amount=item.unit_price.amount,
                    unit_price_currency=item.unit_price.currency,
                )
            )
        self._session.add(model)

    def get(self, id: str) -> Optional[Order]:
        model = self._session.query(OrderModel).filter_by(id=id).first()
        return _order_from_model(model) if model else None

    def list_by_customer(self, customer_id: str) -> List[Order]:
        models = self._session.query(OrderModel).filter_by(customer_id=customer_id).all()
        return [_order_from_model(m) for m in models]

    def update(self, order: Order) -> None:
        model = self._session.query(OrderModel).filter_by(id=order.id).first()
        if not model:
            return
        model.status = order.status.value
        # Sync items (delete old, re-add)
        for item_model in list(model.items):
            self._session.delete(item_model)
        self._session.flush()
        for item in order.items:
            model.items.append(
                OrderItemModel(
                    order_id=order.id,
                    sku=item.sku,
                    quantity=item.quantity,
                    unit_price_amount=item.unit_price.amount,
                    unit_price_currency=item.unit_price.currency,
                )
            )


def _order_from_model(m: OrderModel) -> Order:
    o = Order.__new__(Order)
    o.id = str(m.id)
    o.customer_id = str(m.customer_id)
    o.status = OrderStatus(m.status)
    o.items = [
        OrderItem(
            sku=str(i.sku),
            quantity=int(i.quantity),
            unit_price=Money(
                amount=Decimal(str(i.unit_price_amount)),
                currency=str(i.unit_price_currency),
            ),
        )
        for i in m.items
    ]
    o.events = []
    return o


# ─── Batch (Inventory) ───────────────────────────────────────────────────────

class AbstractBatchRepository(ABC):
    @abstractmethod
    def add(self, batch: Batch) -> None: ...

    @abstractmethod
    def get(self, ref: str) -> Optional[Batch]: ...

    @abstractmethod
    def list(self) -> List[Batch]: ...


class InMemoryBatchRepository(AbstractBatchRepository):
    def __init__(self):
        self._store: List[Batch] = []

    def add(self, batch: Batch) -> None:
        self._store.append(batch)

    def get(self, ref: str) -> Optional[Batch]:
        return next((b for b in self._store if b.ref == ref), None)

    def list(self) -> List[Batch]:
        return list(self._store)


class SqlAlchemyBatchRepository(AbstractBatchRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, batch: Batch) -> None:
        model = BatchModel(
            reference=batch.ref,
            sku=batch.sku,
            quantity=batch.purchased_quantity,
            eta=batch.eta,
        )
        self._session.add(model)

    def get(self, ref: str) -> Optional[Batch]:
        model = self._session.query(BatchModel).filter_by(reference=ref).first()
        return _batch_from_model(model) if model else None

    def list(self) -> List[Batch]:
        return [_batch_from_model(m) for m in self._session.query(BatchModel).all()]


def _batch_from_model(m: BatchModel) -> Batch:
    return Batch(
        ref=str(m.reference),
        sku=str(m.sku),
        purchased_quantity=int(m.quantity),
        eta=m.eta,
    )

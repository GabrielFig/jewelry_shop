"""
Unit tests for domain services — no database, no HTTP, pure Python.
"""
from decimal import Decimal

from app.domain.models import Batch, Category, Customer, Order, OrderLine, OrderStatus, Product
from app.domain.services import allocate
from app.domain.value_objects import Money
from app.unit_of_work import InMemoryUnitOfWork
from app.service_layer import services


# ─── Inventory allocation ─────────────────────────────────────────────────────

def test_allocate_returns_batch_ref():
    batch = Batch(ref="batch1", sku="RING-GOLD-001", purchased_quantity=10)
    line = OrderLine(order_id="order1", sku="RING-GOLD-001", quantity=5)
    ref, _ = allocate(line, [batch])
    assert ref == "batch1"
    assert batch.allocated_quantity == 5


def test_allocate_fails_for_wrong_sku():
    batch = Batch(ref="batch1", sku="RING-SILVER-001", purchased_quantity=10)
    line = OrderLine(order_id="order1", sku="RING-GOLD-001", quantity=5)
    ref, _ = allocate(line, [batch])
    assert ref is None
    assert batch.available_quantity == 10


def test_allocate_fails_for_insufficient_quantity():
    batch = Batch(ref="batch1", sku="RING-GOLD-001", purchased_quantity=4)
    line = OrderLine(order_id="order1", sku="RING-GOLD-001", quantity=5)
    ref, _ = allocate(line, [batch])
    assert ref is None
    assert batch.available_quantity == 4


def test_allocate_order_via_service():
    uow = InMemoryUnitOfWork()
    uow.batches.add(Batch("batch1", "RING-GOLD-001", 10))
    ref = services.allocate_order("order1", "RING-GOLD-001", 2, uow)
    assert ref == "batch1"
    assert uow.committed


# ─── Product domain model ─────────────────────────────────────────────────────

def test_product_price_update():
    product = Product(
        sku="TEST-001",
        name="Test Ring",
        description="",
        price=Money(Decimal("100.00"), "USD"),
        category_id="cat-1",
    )
    product.events.clear()
    product.update_price(Money(Decimal("120.00"), "USD"))
    assert product.price.amount == Decimal("120.00")
    assert len(product.events) == 1


def test_product_deactivate():
    product = Product(
        sku="TEST-002",
        name="Old Ring",
        description="",
        price=Money(Decimal("50.00"), "USD"),
        category_id="cat-1",
    )
    assert product.is_active
    product.deactivate()
    assert not product.is_active


# ─── Order lifecycle ──────────────────────────────────────────────────────────

def test_order_lifecycle():
    order = Order(id="ord-1", customer_id="cust-1")
    price = Money(Decimal("99.99"), "USD")
    order.add_item(sku="RING-GOLD-001", quantity=2, unit_price=price)

    assert order.total.amount == Decimal("199.98")
    assert order.status == OrderStatus.PENDING

    order.confirm()
    assert order.status == OrderStatus.CONFIRMED

    from app.domain.strategies import MockPaymentStrategy
    order.pay(MockPaymentStrategy())
    assert order.status == OrderStatus.PAID

    order.ship()
    assert order.status == OrderStatus.SHIPPED


def test_cannot_add_item_to_confirmed_order():
    order = Order(id="ord-2", customer_id="cust-1")
    order.add_item("RING-001", 1, Money(Decimal("100"), "USD"))
    order.confirm()
    try:
        order.add_item("RING-002", 1, Money(Decimal("50"), "USD"))
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_cannot_cancel_shipped_order():
    order = Order(id="ord-3", customer_id="cust-1")
    order.add_item("RING-001", 1, Money(Decimal("100"), "USD"))
    order.confirm()
    from app.domain.strategies import MockPaymentStrategy
    order.pay(MockPaymentStrategy())
    order.ship()
    try:
        order.cancel()
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ─── Category / Product services (in-memory) ─────────────────────────────────

def test_create_category_via_service():
    uow = InMemoryUnitOfWork()
    cat = services.create_category("Rings", "Finger rings", uow)
    assert cat.name == "Rings"
    assert uow.committed


def test_create_product_via_service():
    uow = InMemoryUnitOfWork()
    cat = services.create_category("Rings", "", uow)
    product = services.create_product(
        sku="RING-001",
        name="Gold Ring",
        description="",
        price_amount=Decimal("299.00"),
        price_currency="USD",
        category_id=cat.id,
        attributes={"material": "gold"},
        image_url="",
        uow=uow,
    )
    assert product.sku == "RING-001"
    assert product.price.amount == Decimal("299.00")


def test_create_customer_via_service():
    uow = InMemoryUnitOfWork()
    customer = services.create_customer("alice@example.com", "Alice", uow)
    assert customer.email == "alice@example.com"
    assert uow.committed


def test_full_order_flow_via_service():
    uow = InMemoryUnitOfWork()
    cat = services.create_category("Rings", "", uow)
    services.create_product(
        sku="RING-001", name="Ring", description="",
        price_amount=Decimal("100.00"), price_currency="USD",
        category_id=cat.id, attributes={}, image_url="", uow=uow,
    )
    customer = services.create_customer("bob@example.com", "Bob", uow)
    order = services.create_order(customer.id, uow)
    order = services.add_item_to_order(order.id, "RING-001", 1, uow)
    order = services.confirm_order(order.id, uow)
    order = services.pay_order(order.id, payment_method="mock", uow=uow)
    assert order.status == OrderStatus.PAID
    assert order.total.amount == Decimal("100.00")

"""
Tests for domain event publishing via the message bus.
"""
from decimal import Decimal

from app.domain.models import Batch, OrderStatus
from app.domain.value_objects import Money
from app.message_bus import SENT_NOTIFICATIONS
from app.unit_of_work import InMemoryUnitOfWork
from app.service_layer import services


def setup_function():
    SENT_NOTIFICATIONS.clear()


def test_order_allocated_event_published():
    uow = InMemoryUnitOfWork()
    uow.batches.add(Batch("batch1", "RING-001", 5))
    ref = services.allocate_order("order1", "RING-001", 2, uow)
    assert ref == "batch1"
    assert any("RING-001" in n for n in SENT_NOTIFICATIONS)
    assert any("batch1" in n for n in SENT_NOTIFICATIONS)


def test_out_of_stock_event_published():
    uow = InMemoryUnitOfWork()
    try:
        services.allocate_order("order1", "RING-MISSING", 1, uow)
    except ValueError:
        pass
    assert any("Out of stock" in n for n in SENT_NOTIFICATIONS)


def test_order_paid_event_notification():
    uow = InMemoryUnitOfWork()
    cat = services.create_category("Test", "", uow)
    services.create_product(
        sku="SKU-1", name="Item", description="",
        price_amount=Decimal("50.00"), price_currency="USD",
        category_id=cat.id, attributes={}, image_url="", uow=uow,
    )
    customer = services.create_customer("test@test.com", "Test", uow)
    order = services.create_order(customer.id, uow)
    order = services.add_item_to_order(order.id, "SKU-1", 1, uow)
    order = services.confirm_order(order.id, uow)
    SENT_NOTIFICATIONS.clear()
    services.pay_order(order.id, payment_method="mock", uow=uow)
    assert any("paid" in n.lower() for n in SENT_NOTIFICATIONS)

from app.unit_of_work import InMemoryUnitOfWork
from app.domain.models import Batch
from app.service_layer.services import allocate_order
from app.message_bus import SENT_NOTIFICATIONS

def test_order_allocated_event():
    uow = InMemoryUnitOfWork()
    uow.batches.add(Batch("b-1", "GOLD_RING", 5))
    SENT_NOTIFICATIONS.clear()

    ref = allocate_order("o-1", "GOLD_RING", 2, uow)

    assert ref == "b-1"
    assert any("Allocated order o-1" in msg for msg in SENT_NOTIFICATIONS)

def test_out_of_stock_event():
    uow = InMemoryUnitOfWork()
    SENT_NOTIFICATIONS.clear()

    try:
        allocate_order("o-2", "SILVER_CHAIN", 1, uow)
    except Exception:
        pass

    assert any("Out of stock for sku SILVER_CHAIN" in msg for msg in SENT_NOTIFICATIONS)

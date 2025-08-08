from app.domain.models import Batch, OrderLine
from app.domain.services import allocate
from app.unit_of_work import InMemoryUnitOfWork
from app.service_layer.services import allocate_order


def test_returns_allocated_batch_ref():
    batch = Batch(ref="batch1", sku="GOLD_RING", purchased_quantity=10)
    line = OrderLine(order_id="order1", sku="GOLD_RING", quantity=5)
    
    result = allocate(line, [batch])
    
    assert result == "batch1"
    assert batch.allocated_quantity == 5


def test_allocation_fails_for_wrong_sku():
    batch = Batch(ref="batch1", sku="SILVER_RING", purchased_quantity=10)
    line = OrderLine(order_id="order1", sku="GOLD_RING", quantity=5)
    result = allocate(line, [batch])

    assert result is None
    assert batch.available_quantity == 10


def test_allocation_fails_for_insufficient_quantity():
    batch = Batch(ref="batch1", sku="GOLD_RING", purchased_quantity=4)
    line = OrderLine(order_id="order1", sku="GOLD_RING", quantity=5)
    result = allocate(line, [batch])

    assert result is None
    assert batch.available_quantity == 5


def test_allocate_order():
    uow = InMemoryUnitOfWork()
    uow.batches.add(Batch("batch1", "GOLD_RING", 10))
    result = allocate_order("order1", "GOLD_RING", 2, uow)

    assert result == "batch1"
    assert uow.committed

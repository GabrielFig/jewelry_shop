from app.domain.models import OrderLine
from app.domain.services import allocate
from app.domain.events import OrderAllocated, OutOfStock
from app.unit_of_work import AbstractUnitOfWork
from app.message_bus import publish




def allocate_order(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(order_id=order_id, sku=sku, quantity=qty)
    with uow:
        batches = uow.batches.list()
        batch_ref_tuple = allocate(line, batches)
        batch_ref = batch_ref_tuple[0]  # Extract the batch reference (str or None)
        if not batch_ref:
            publish(OutOfStock(sku=sku))  # 🔴 Evento publicado aquí
            raise Exception("Out of stock")
        publish(OrderAllocated(order_id=order_id, sku=sku, quantity=qty, batch_ref=batch_ref))
        uow.commit()
        return batch_ref

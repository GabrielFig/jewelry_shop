from app.domain.models import OrderLine
from app.domain.services import allocate
from app.unit_of_work import AbstractUnitOfWork



def allocate_order(order_id: str, sku: str, quantity: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(order_id=order_id, sku=sku, quantity=quantity)
    with uow:
        batches = uow.batches.list()
        batch_ref = allocate(line, batches)
        if not batch_ref:
            raise ValueError("Out of stock")
        uow.commit()
        return batch_ref
    
from typing import List, Optional
from app.domain.models import Batch, OrderLine
from app.domain import events

from typing import Tuple




def allocate(line: OrderLine, batches: List[Batch]):
    for batch in batches:
        if batch.can_allocate(line):
            batch.allocate(line)
            event = events.OrderAllocated(
                order_id=line.order_id,
                sku=line.sku,
                quantity=line.quantity,
                batch_ref=batch.ref
            )
            return batch.ref, [event]
    event = events.OutOfStock(sku=line.sku)
    return None, [event]
        
"""
Pure domain services — stateless functions that operate on domain objects.
No I/O, no framework imports.
"""
from datetime import date
from typing import List, Optional, Tuple

from app.domain.models import Batch, OrderLine
from app.domain import events


def allocate(line: OrderLine, batches: List[Batch]) -> Tuple[Optional[str], list]:
    """
    Allocate an order line to the earliest available batch that can fulfil it.

    Batches without an ETA (in-stock) are preferred over batches with a future
    ETA (on order).  Within the same ETA tier, order is unspecified.

    Returns (batch_ref, [events]).  If no batch can fulfil the line,
    batch_ref is None and an OutOfStock event is included.
    """
    def sort_key(b: Batch) -> date:
        return b.eta if b.eta is not None else date.min

    sorted_batches = sorted(batches, key=sort_key)

    for batch in sorted_batches:
        if batch.can_allocate(line):
            batch.allocate(line)
            event = events.OrderAllocated(
                order_id=line.order_id,
                sku=line.sku,
                quantity=line.quantity,
                batch_ref=batch.ref,
            )
            return batch.ref, [event]

    return None, [events.OutOfStock(sku=line.sku)]

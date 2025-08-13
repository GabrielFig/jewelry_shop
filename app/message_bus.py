from typing import Callable, Dict, List, Type, Any
from app.domain.events import OrderAllocated, OutOfStock


SENT_NOTIFICATIONS: List[str] = []


def handle_order_allocated(event: OrderAllocated):
    SENT_NOTIFICATIONS.append(
        f"Allocated order {event.order_id} to batch {event.batch_ref} for SKU {event.sku} with quantity {event.quantity}"
    )

def handle_out_of_stock(event: OutOfStock):
    SENT_NOTIFICATIONS.append(
        f"Out of stock for SKU {event.sku}"
    )


HANDLERS: Dict[Type[Any], List[Callable[[Any], None]]] = {
    OrderAllocated: [handle_order_allocated],
    OutOfStock: [handle_out_of_stock]
}


def publish(event: Any):
    for handler in HANDLERS.get(type(event), []):
        handler(event)
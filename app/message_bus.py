"""
Message Bus — dispatches domain events to registered handlers.

How it works:
  1. A domain operation (service layer function) collects events from
     domain models after committing the Unit of Work.
  2. The caller passes those events to publish() or publish_all().
  3. The bus looks up registered handlers and calls each one.

Registering a new handler:
    from app.domain.events import SomeNewEvent
    from app.message_bus import HANDLERS

    def handle_some_new_event(event: SomeNewEvent) -> None:
        ...

    HANDLERS[SomeNewEvent].append(handle_some_new_event)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type

from app.domain import events
from app.service_layer import handlers
from app.notifications import SENT_NOTIFICATIONS  # re-exported for API convenience

logger = logging.getLogger(__name__)

__all__ = ["HANDLERS", "SENT_NOTIFICATIONS", "publish", "publish_all"]

# ─── Handler registry ─────────────────────────────────────────────────────────

HANDLERS: Dict[Type[Any], List[Callable[[Any], None]]] = defaultdict(list, {
    # Inventory
    events.OrderAllocated: [handlers.on_order_allocated],
    events.OutOfStock: [handlers.on_out_of_stock],
    events.BatchAdded: [handlers.on_batch_added],
    # Catalog
    events.ProductCreated: [handlers.on_product_created],
    events.ProductPriceChanged: [handlers.on_product_price_changed],
    # Customers
    events.CustomerCreated: [handlers.on_customer_created],
    # Orders
    events.OrderCreated: [handlers.on_order_created],
    events.OrderConfirmed: [handlers.on_order_confirmed],
    events.OrderPaid: [handlers.on_order_paid],
    events.OrderShipped: [handlers.on_order_shipped],
    events.OrderCancelled: [handlers.on_order_cancelled],
})


def publish(event: Any) -> None:
    """Dispatch a single domain event to all registered handlers."""
    for handler in HANDLERS.get(type(event), []):
        try:
            handler(event)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Handler %s failed for event %s: %s",
                handler.__name__,
                event,
                exc,
                exc_info=True,
            )


def publish_all(event_list: list) -> None:
    """Dispatch every event in a list."""
    for event in event_list:
        publish(event)

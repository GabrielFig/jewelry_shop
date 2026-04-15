"""
Event handlers — side effects triggered by domain events.

Handlers are registered in app/message_bus.py.  They should be idempotent
and must never raise exceptions that would propagate to the caller (log instead).

Extend this file to add real side effects:
  - Send emails / push notifications
  - Update search indexes
  - Publish to an external message queue (Kafka, RabbitMQ, etc.)
  - Write audit logs
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.notifications import SENT_NOTIFICATIONS

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.domain import events


# ─── Inventory handlers ───────────────────────────────────────────────────────

def on_order_allocated(event: "events.OrderAllocated") -> None:
    msg = (
        f"[INVENTORY] Order '{event.order_id}' allocated to batch '{event.batch_ref}' "
        f"| SKU: {event.sku} | Qty: {event.quantity}"
    )
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_out_of_stock(event: "events.OutOfStock") -> None:
    msg = f"[INVENTORY] Out of stock for SKU: {event.sku}"
    logger.warning(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_batch_added(event: "events.BatchAdded") -> None:
    msg = f"[INVENTORY] New batch '{event.ref}' added | SKU: {event.sku} | Qty: {event.quantity}"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


# ─── Catalog handlers ─────────────────────────────────────────────────────────

def on_product_created(event: "events.ProductCreated") -> None:
    msg = (
        f"[CATALOG] New product '{event.name}' (SKU: {event.sku}) "
        f"created in category {event.category_id}"
    )
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_product_price_changed(event: "events.ProductPriceChanged") -> None:
    msg = (
        f"[CATALOG] Price updated for SKU '{event.sku}': "
        f"{event.currency} {event.old_price_amount} → {event.currency} {event.new_price_amount}"
    )
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


# ─── Customer handlers ────────────────────────────────────────────────────────

def on_customer_created(event: "events.CustomerCreated") -> None:
    msg = f"[CUSTOMER] New customer '{event.name}' registered | email: {event.email}"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


# ─── Order handlers ───────────────────────────────────────────────────────────

def on_order_created(event: "events.OrderCreated") -> None:
    msg = f"[ORDER] Order '{event.order_id}' created for customer '{event.customer_id}'"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_order_confirmed(event: "events.OrderConfirmed") -> None:
    msg = f"[ORDER] Order '{event.order_id}' confirmed"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_order_paid(event: "events.OrderPaid") -> None:
    msg = f"[ORDER] Order '{event.order_id}' paid | Amount: {event.currency} {event.amount}"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_order_shipped(event: "events.OrderShipped") -> None:
    msg = f"[ORDER] Order '{event.order_id}' shipped"
    logger.info(msg)
    SENT_NOTIFICATIONS.append(msg)


def on_order_cancelled(event: "events.OrderCancelled") -> None:
    msg = f"[ORDER] Order '{event.order_id}' cancelled"
    logger.warning(msg)
    SENT_NOTIFICATIONS.append(msg)

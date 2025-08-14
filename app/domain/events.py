from dataclasses import dataclass


@dataclass(frozen=True)
class OrderAllocated:
    order_id: str
    sku: str
    quantity: int
    batch_ref: str


@dataclass(frozen=True)
class OutOfStock:
    sku: str

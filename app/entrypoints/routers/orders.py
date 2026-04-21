from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, require_admin
from app.domain.models import User
from app.service_layer import services
from app.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/orders", tags=["Orders"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class OrderCreateIn(BaseModel):
    customer_id: str


class AddItemIn(BaseModel):
    sku: str
    quantity: int


class PayOrderIn(BaseModel):
    """
    payment_method options (built-in):
      - "mock"        → always succeeds, use in dev/testing
      - "credit_card" → placeholder for real gateway; pass token in extra_params
    """
    payment_method: str = "mock"
    extra_params: Optional[dict] = None


class OrderItemOut(BaseModel):
    sku: str
    quantity: int
    unit_price_amount: Decimal
    unit_price_currency: str
    subtotal: Decimal


class OrderOut(BaseModel):
    id: str
    customer_id: str
    status: str
    items: List[OrderItemOut]
    total_amount: Decimal
    total_currency: str


def _to_out(order) -> OrderOut:
    items = [
        OrderItemOut(
            sku=i.sku,
            quantity=i.quantity,
            unit_price_amount=i.unit_price.amount,
            unit_price_currency=i.unit_price.currency,
            subtotal=i.subtotal.amount,
        )
        for i in order.items
    ]
    total = order.total
    return OrderOut(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status.value,
        items=items,
        total_amount=total.amount,
        total_currency=total.currency,
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreateIn, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.create_order(body.customer_id, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: str, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.get_order(order_id, uow)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return _to_out(order)


@router.get("/customer/{customer_id}", response_model=List[OrderOut])
def list_customer_orders(customer_id: str, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        orders = services.list_customer_orders(customer_id, uow)
    return [_to_out(o) for o in orders]


@router.post("/{order_id}/items", response_model=OrderOut)
def add_item(order_id: str, body: AddItemIn, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.add_item_to_order(order_id, body.sku, body.quantity, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)


@router.post("/{order_id}/confirm", response_model=OrderOut)
def confirm_order(order_id: str, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.confirm_order(order_id, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)


@router.post("/{order_id}/pay", response_model=OrderOut)
def pay_order(order_id: str, body: PayOrderIn, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.pay_order(
                order_id,
                payment_method=body.payment_method,
                uow=uow,
                **(body.extra_params or {}),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)


@router.post("/{order_id}/ship", response_model=OrderOut)
def ship_order(order_id: str, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.ship_order(order_id, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: str, _: User = Depends(get_current_user)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            order = services.cancel_order(order_id, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(order)

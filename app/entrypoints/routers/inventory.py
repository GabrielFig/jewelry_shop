from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.domain.models import User
from app.service_layer import services
from app.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class BatchIn(BaseModel):
    reference: str
    sku: str
    quantity: int
    eta: Optional[date] = None


class BatchOut(BaseModel):
    reference: str
    sku: str
    purchased_quantity: int
    available_quantity: int
    eta: Optional[date]


class AllocateIn(BaseModel):
    order_id: str
    sku: str
    quantity: int


@router.post("/batches", response_model=BatchOut, status_code=201)
def add_batch(body: BatchIn, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            batch = services.add_batch(
                ref=body.reference,
                sku=body.sku,
                quantity=body.quantity,
                eta=body.eta,
                uow=uow,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return BatchOut(
        reference=batch.ref,
        sku=batch.sku,
        purchased_quantity=batch.purchased_quantity,
        available_quantity=batch.available_quantity,
        eta=batch.eta,
    )


@router.get("/batches", response_model=List[BatchOut])
def list_batches(_: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        batches = uow.batches.list()
    return [
        BatchOut(
            reference=b.ref,
            sku=b.sku,
            purchased_quantity=b.purchased_quantity,
            available_quantity=b.available_quantity,
            eta=b.eta,
        )
        for b in batches
    ]


@router.post("/allocate")
def allocate(body: AllocateIn, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            batch_ref = services.allocate_order(
                order_id=body.order_id,
                sku=body.sku,
                qty=body.quantity,
                uow=uow,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"batch_ref": batch_ref}

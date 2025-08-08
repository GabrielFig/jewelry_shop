from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service_layer.services import allocate_order
from app.unit_of_work import InMemoryUnitOfWork
from app.domain.models import Batch
from datetime import date
from typing import Optional
from app.unit_of_work import SqlAlchemyUnitOfWork


router = APIRouter()

uow = InMemoryUnitOfWork()
uow.batches.add(Batch("batch-001", "GOLD_RING", 10))
uow.batches.add(Batch("batch-002", "SILVER_RING", 5))

class OrderRequest(BaseModel):
    order_id: str
    sku: str
    quantity: int


class BatchRequest(BaseModel):
    reference: str
    sku: str
    quantity: int
    eta: Optional[date] = None

@router.post("/allocate")
def allocate(request: OrderRequest):
    
    try:
        batch_ref = allocate_order(
            request.order_id, 
            request.sku, 
            request.quantity, 
            uow
        )
        return {"batch_ref": batch_ref}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches")
def add_batch(batch: BatchRequest):
    with SqlAlchemyUnitOfWork() as uow:
        existing = uow.batches.get(batch.reference)
        if existing:
            raise HTTPException(status_code=400, detail="Batch already exists")
        
        domain_batch = Batch(
            ref=batch.reference,
            sku=batch.sku,
            purchased_quantity=batch.quantity
        )
        uow.batches.add(domain_batch)
        uow.commit()
    return {"message": f"Batch {batch.reference} added."}
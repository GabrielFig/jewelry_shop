from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service_layer.services import allocate_order
from app.unit_of_work import InMemoryUnitOfWork
from app.domain.models import Batch


router = APIRouter()

uow = InMemoryUnitOfWork()
uow.batches.add(Batch("batch-001", "GOLD_RING", 10))
uow.batches.add(Batch("batch-002", "SILVER_RING", 5))

class OrderRequest(BaseModel):
    order_id: str
    sku: str
    quantity: int


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
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.auth.dependencies import require_admin
from app.domain.models import User
from app.service_layer import services
from app.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerIn(BaseModel):
    email: EmailStr
    name: str


class CustomerOut(BaseModel):
    id: str
    email: str
    name: str


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerIn, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            customer = services.create_customer(body.email, body.name, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return CustomerOut(id=customer.id, email=customer.email, name=customer.name)


@router.get("", response_model=list[CustomerOut])
def list_customers(_: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        customers = services.list_customers(uow)
    return [CustomerOut(id=c.id, email=c.email, name=c.name) for c in customers]


@router.get("/{id}", response_model=CustomerOut)
def get_customer(id: str, _: User = Depends(require_admin)):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            customer = services.get_customer(id, uow)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return CustomerOut(id=customer.id, email=customer.email, name=customer.name)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.service_layer import services
from app.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryIn(BaseModel):
    name: str
    description: str = ""


class CategoryOut(BaseModel):
    id: str
    name: str
    description: str


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryIn):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            cat = services.create_category(body.name, body.description, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return CategoryOut(id=cat.id, name=cat.name, description=cat.description)


@router.get("", response_model=list[CategoryOut])
def list_categories():
    with SqlAlchemyUnitOfWork() as uow:
        cats = services.list_categories(uow)
    return [CategoryOut(id=c.id, name=c.name, description=c.description) for c in cats]


@router.get("/{id}", response_model=CategoryOut)
def get_category(id: str):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            cat = services.get_category(id, uow)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return CategoryOut(id=cat.id, name=cat.name, description=cat.description)

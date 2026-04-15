from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.service_layer import services
from app.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/products", tags=["Products"])


class ProductIn(BaseModel):
    sku: str
    name: str
    description: str = ""
    price_amount: Decimal
    price_currency: str = "USD"
    category_id: str
    # Domain-extensibility hook: any key-value pairs relevant to the product type.
    # Jewelry example: {"material": "18k gold", "gemstone": "emerald", "weight_g": 4.5}
    attributes: Optional[Dict[str, Any]] = None
    image_url: str = ""


class PriceUpdateIn(BaseModel):
    amount: Decimal
    currency: str = "USD"


class ProductOut(BaseModel):
    sku: str
    name: str
    description: str
    price_amount: Decimal
    price_currency: str
    category_id: str
    attributes: Dict[str, Any]
    image_url: str
    is_active: bool


def _to_out(p) -> ProductOut:
    return ProductOut(
        sku=p.sku,
        name=p.name,
        description=p.description,
        price_amount=p.price.amount,
        price_currency=p.price.currency,
        category_id=p.category_id,
        attributes=p.attributes,
        image_url=p.image_url,
        is_active=p.is_active,
    )


@router.post("", response_model=ProductOut, status_code=201)
def create_product(body: ProductIn):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            product = services.create_product(
                sku=body.sku,
                name=body.name,
                description=body.description,
                price_amount=body.price_amount,
                price_currency=body.price_currency,
                category_id=body.category_id,
                attributes=body.attributes,
                image_url=body.image_url,
                uow=uow,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(product)


@router.get("", response_model=List[ProductOut])
def list_products(
    category_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    with SqlAlchemyUnitOfWork() as uow:
        products = services.list_products(uow, category_id=category_id, active_only=active_only)
    return [_to_out(p) for p in products]


@router.get("/{sku}", response_model=ProductOut)
def get_product(sku: str):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            product = services.get_product(sku, uow)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return _to_out(product)


@router.patch("/{sku}/price", response_model=ProductOut)
def update_price(sku: str, body: PriceUpdateIn):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            product = services.update_product_price(sku, body.amount, body.currency, uow)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return _to_out(product)


@router.delete("/{sku}", status_code=204)
def deactivate_product(sku: str):
    with SqlAlchemyUnitOfWork() as uow:
        try:
            services.deactivate_product(sku, uow)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

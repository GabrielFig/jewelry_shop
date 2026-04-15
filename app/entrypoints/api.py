from fastapi import APIRouter

from app.entrypoints.routers import categories, customers, inventory, orders, products
from app.notifications import SENT_NOTIFICATIONS

router = APIRouter()

# Mount domain-specific sub-routers
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(customers.router)
router.include_router(orders.router)
router.include_router(inventory.router)


@router.get("/notifications", tags=["System"])
def get_notifications():
    """Returns all domain event notifications published in this session."""
    return {"count": len(SENT_NOTIFICATIONS), "notifications": SENT_NOTIFICATIONS}


@router.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}

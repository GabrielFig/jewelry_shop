import pytest
from fastapi.testclient import TestClient
from main import app
from app.notifications import SENT_NOTIFICATIONS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.adapters.sqlalchemy_models import Base, BatchModel

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_notifications():
    SENT_NOTIFICATIONS.clear()
    yield
    SENT_NOTIFICATIONS.clear()

@pytest.fixture(autouse=True)
def clean_batches():
    engine = create_engine("sqlite:///./jewelry.db", connect_args={"check_same_thread": False})
    # Drop and recreate to pick up any schema changes
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_add_batch_and_allocate():
    response = client.post("/inventory/batches", json={
        "reference": "batch-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 5,
    })
    assert response.status_code == 201

    response = client.post("/inventory/allocate", json={
        "order_id": "order-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 2,
    })
    assert response.status_code == 200
    assert response.json()["batch_ref"] == "batch-test-1"

    notifications = client.get("/notifications").json()["notifications"]
    assert any("order-test-1" in msg for msg in notifications)


def test_allocate_out_of_stock():
    response = client.post("/inventory/allocate", json={
        "order_id": "order-no-stock",
        "sku": "DIAMOND_NECKLACE",
        "quantity": 1,
    })
    assert response.status_code == 400
    assert "stock" in response.text.lower()

    notifications = client.get("/notifications").json()["notifications"]
    assert any("Out of stock" in msg for msg in notifications)

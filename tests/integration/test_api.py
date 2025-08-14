import pytest
from fastapi.testclient import TestClient
from main import app
from app.message_bus import SENT_NOTIFICATIONS
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
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    session.query(BatchModel).delete()
    session.commit()
    session.close()
    yield

def test_add_batch_and_allocate():
    # Agregar un batch
    response = client.post("/batches", json={
        "reference": "batch-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 5
    })
    assert response.status_code == 200
    assert "Batch batch-test-1 added." in response.json()["message"]

    # Asignar un pedido
    response = client.post("/allocate", json={
        "order_id": "order-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 2
    })
    assert response.status_code == 200
    assert response.json()["batch_ref"] == "batch-test-1"

    # Verificar notificación
    response = client.get("/notifications")
    assert response.status_code == 200
    notifications = response.json()["notifications"]
    assert any("Allocated order order-test-1" in msg for msg in notifications)

def test_allocate_out_of_stock():
    response = client.post("/allocate", json={
        "order_id": "order-no-stock",
        "sku": "DIAMOND_NECKLACE",
        "quantity": 1
    })
    assert response.status_code == 400
    assert "Out of stock" in response.text

    # Verificar notificación de evento
    notifications = client.get("/notifications").json()["notifications"]
    assert any("Out of stock for sku DIAMOND_NECKLACE" in msg for msg in notifications)
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.sqlalchemy_models import Base
from app.auth.hashing import hash_password
from app.notifications import SENT_NOTIFICATIONS
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_notifications():
    SENT_NOTIFICATIONS.clear()
    yield
    SENT_NOTIFICATIONS.clear()


@pytest.fixture(autouse=True)
def clean_db():
    engine = create_engine("sqlite:///./jewelry.db", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed an admin user so auth-protected endpoints can be exercised
    from app.adapters.sqlalchemy_models import UserModel
    Session = sessionmaker(bind=engine)
    with Session() as session:
        admin = UserModel(
            id=str(uuid.uuid4()),
            email="testadmin@test.com",
            hashed_password=hash_password("TestAdmin123!"),
            name="Test Admin",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()

    yield
    Base.metadata.drop_all(bind=engine)


def _admin_headers() -> dict:
    resp = client.post("/auth/login", json={"email": "testadmin@test.com", "password": "TestAdmin123!"})
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_add_batch_and_allocate():
    headers = _admin_headers()

    response = client.post("/inventory/batches", json={
        "reference": "batch-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 5,
    }, headers=headers)
    assert response.status_code == 201

    response = client.post("/inventory/allocate", json={
        "order_id": "order-test-1",
        "sku": "GOLD_NECKLACE",
        "quantity": 2,
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["batch_ref"] == "batch-test-1"

    notifications = client.get("/notifications", headers=headers).json()["notifications"]
    assert any("order-test-1" in msg for msg in notifications)


def test_allocate_out_of_stock():
    headers = _admin_headers()

    response = client.post("/inventory/allocate", json={
        "order_id": "order-no-stock",
        "sku": "DIAMOND_NECKLACE",
        "quantity": 1,
    }, headers=headers)
    assert response.status_code == 400
    assert "stock" in response.text.lower()

    notifications = client.get("/notifications", headers=headers).json()["notifications"]
    assert any("Out of stock" in msg for msg in notifications)

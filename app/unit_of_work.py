"""
Unit of Work pattern — groups repository operations into a single atomic transaction.

Usage (in service layer):
    def some_service(uow: AbstractUnitOfWork):
        product = uow.products.get("GOLD-RING-001")
        product.update_price(Money(Decimal("499.99"), "USD"))
        uow.products.update(product)
        uow.commit()

The UoW owns the session/transaction; the caller decides when to commit or roll back.
The entrypoints (API routes) are responsible for the context manager lifecycle:

    with SqlAlchemyUnitOfWork() as uow:
        some_service(uow)
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (works both locally and inside Docker)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.repository import (
    AbstractBatchRepository,
    AbstractCategoryRepository,
    AbstractCustomerRepository,
    AbstractOrderRepository,
    AbstractProductRepository,
    AbstractUserRepository,
    InMemoryBatchRepository,
    InMemoryCategoryRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
    InMemoryUserRepository,
    SqlAlchemyBatchRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyUserRepository,
)

def _build_database_url() -> str:
    # 1. Prefer an explicit DATABASE_URL if set
    if url := os.getenv("DATABASE_URL"):
        return url
    # 2. Build from individual parts (useful when running locally with .env)
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ecommerce")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class AbstractUnitOfWork(ABC):
    categories: AbstractCategoryRepository
    products: AbstractProductRepository
    customers: AbstractCustomerRepository
    orders: AbstractOrderRepository
    batches: AbstractBatchRepository
    users: AbstractUserRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    def collect_events(self) -> list:
        """Collect all pending domain events from tracked aggregates."""
        return []


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """
    In-memory UoW for unit tests — no database required.
    All repositories store data in Python lists.
    """

    def __init__(self):
        self.categories = InMemoryCategoryRepository()
        self.products = InMemoryProductRepository()
        self.customers = InMemoryCustomerRepository()
        self.orders = InMemoryOrderRepository()
        self.batches = InMemoryBatchRepository()
        self.users = InMemoryUserRepository()
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy-backed UoW for production use.
    Opens a session on __enter__ and closes it on __exit__.
    """

    def __init__(self):
        self._session = SessionLocal()
        self.categories = SqlAlchemyCategoryRepository(self._session)
        self.products = SqlAlchemyProductRepository(self._session)
        self.customers = SqlAlchemyCustomerRepository(self._session)
        self.orders = SqlAlchemyOrderRepository(self._session)
        self.batches = SqlAlchemyBatchRepository(self._session)
        self.users = SqlAlchemyUserRepository(self._session)
        self.committed = False

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    def __exit__(self, *args) -> None:
        if not self.committed:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()
        self.committed = True

    def rollback(self) -> None:
        self._session.rollback()

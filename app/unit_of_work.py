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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.repository import (
    AbstractBatchRepository,
    AbstractCategoryRepository,
    AbstractCustomerRepository,
    AbstractOrderRepository,
    AbstractProductRepository,
    InMemoryBatchRepository,
    InMemoryCategoryRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
    SqlAlchemyBatchRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/ecommerce",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class AbstractUnitOfWork(ABC):
    categories: AbstractCategoryRepository
    products: AbstractProductRepository
    customers: AbstractCustomerRepository
    orders: AbstractOrderRepository
    batches: AbstractBatchRepository

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

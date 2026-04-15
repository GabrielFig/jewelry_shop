"""
SQLAlchemy ORM models — infrastructure layer, not domain models.

Domain objects are converted to/from these models inside the repository
implementations.  The domain layer never imports from this module.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ─── Catalog ─────────────────────────────────────────────────────────────────

class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, default="")

    products = relationship("ProductModel", back_populates="category", lazy="dynamic")


class ProductModel(Base):
    __tablename__ = "products"

    sku = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    price_amount = Column(Numeric(12, 2), nullable=False)
    price_currency = Column(String(3), nullable=False, default="USD")
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    # Stores any domain-specific attributes as a JSON blob.
    # This is the extensibility hook for non-jewelry e-commerce.
    attributes = Column(JSON, default=dict)
    image_url = Column(String(500), default="")
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("CategoryModel", back_populates="products")


# ─── Customers ───────────────────────────────────────────────────────────────

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

    orders = relationship("OrderModel", back_populates="customer", lazy="dynamic")


# ─── Orders ──────────────────────────────────────────────────────────────────

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("CustomerModel", back_populates="orders")
    items = relationship("OrderItemModel", back_populates="order", cascade="all, delete-orphan")


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    sku = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_amount = Column(Numeric(12, 2), nullable=False)
    unit_price_currency = Column(String(3), nullable=False, default="USD")

    order = relationship("OrderModel", back_populates="items")


# ─── Users ───────────────────────────────────────────────────────────────────

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")
    is_active = Column(Boolean, default=True, nullable=False)


# ─── Inventory ───────────────────────────────────────────────────────────────

class BatchModel(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference = Column(String(255), unique=True, nullable=False)
    sku = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    eta = Column(Date, nullable=True)

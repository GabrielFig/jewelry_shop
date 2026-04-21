"""
Database initialisation — creates all tables defined in the ORM models.
Run this once before starting the application.

Usage:
    python init_db.py           # create tables only
    python init_db.py --seed    # create tables + insert sample data
"""
import sys

from app.adapters.sqlalchemy_models import Base
from app.unit_of_work import engine


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


def seed_data():
    """Insert sample jewelry-shop data to get started quickly."""
    from app.service_layer import services
    from app.unit_of_work import SqlAlchemyUnitOfWork

    print("Seeding sample data...")

    # ── Categories ─────────────────────────────────────────────────────────
    with SqlAlchemyUnitOfWork() as uow:
        try:
            rings = services.create_category("Rings", "Finger rings of all styles", uow)
            necklaces = services.create_category("Necklaces", "Chains and pendants", uow)
            earrings = services.create_category("Earrings", "Studs, hoops and drops", uow)
        except ValueError:
            # Already seeded
            print("Categories already exist, skipping.")
            return

    # ── Products ───────────────────────────────────────────────────────────
    with SqlAlchemyUnitOfWork() as uow:
        services.create_product(
            sku="RING-GOLD-001",
            name="18k Gold Solitaire Ring",
            description="Classic solitaire with a 0.5ct diamond, 18k yellow gold band.",
            price_amount=__import__("decimal").Decimal("899.99"),
            price_currency="USD",
            category_id=rings.id,
            attributes={
                "material": "18k gold",
                "gemstone": "diamond",
                "gemstone_weight_ct": 0.5,
                "ring_size": "7",
                "weight_g": 4.2,
            },
            image_url="https://example.com/images/ring-gold-001.jpg",
            uow=uow,
        )
        services.create_product(
            sku="RING-SILVER-001",
            name="Sterling Silver Band",
            description="Minimalist polished sterling silver band, hypoallergenic.",
            price_amount=__import__("decimal").Decimal("59.99"),
            price_currency="USD",
            category_id=rings.id,
            attributes={
                "material": "sterling silver",
                "gemstone": None,
                "ring_size": "7",
                "weight_g": 3.1,
            },
            image_url="",
            uow=uow,
        )
        services.create_product(
            sku="NECK-GOLD-001",
            name="Gold Heart Necklace",
            description="Delicate 14k gold heart pendant on a 45cm chain.",
            price_amount=__import__("decimal").Decimal("349.00"),
            price_currency="USD",
            category_id=necklaces.id,
            attributes={
                "material": "14k gold",
                "chain_length_cm": 45,
                "pendant": "heart",
                "weight_g": 2.8,
            },
            image_url="",
            uow=uow,
        )
        services.create_product(
            sku="EARR-PEARL-001",
            name="Freshwater Pearl Studs",
            description="8mm freshwater pearl studs with sterling silver posts.",
            price_amount=__import__("decimal").Decimal("79.99"),
            price_currency="USD",
            category_id=earrings.id,
            attributes={
                "material": "sterling silver",
                "gemstone": "pearl",
                "pearl_size_mm": 8,
                "style": "studs",
            },
            image_url="",
            uow=uow,
        )

    # ── Inventory batches ──────────────────────────────────────────────────
    with SqlAlchemyUnitOfWork() as uow:
        services.add_batch("BATCH-RING-GOLD-001", "RING-GOLD-001", 20, None, uow)
        services.add_batch("BATCH-RING-SILVER-001", "RING-SILVER-001", 50, None, uow)
        services.add_batch("BATCH-NECK-GOLD-001", "NECK-GOLD-001", 15, None, uow)
        services.add_batch("BATCH-EARR-PEARL-001", "EARR-PEARL-001", 30, None, uow)

    print("Sample data seeded successfully.")


def create_default_admin():
    """Create a default admin account if none exists."""
    import os
    import uuid
    from app.auth.hashing import hash_password
    from app.domain.models import User, UserRole
    from app.unit_of_work import SqlAlchemyUnitOfWork

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set — skipping default admin creation.")
        return

    with SqlAlchemyUnitOfWork() as uow:
        if uow.users.get_by_email(admin_email):
            print(f"Admin '{admin_email}' already exists, skipping.")
            return
        user = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            hashed_password=hash_password(admin_password),
            name="Store Admin",
            role=UserRole.ADMIN,
        )
        uow.users.add(user)
        uow.commit()
    print(f"Default admin created: {admin_email}")


if __name__ == "__main__":
    create_tables()
    create_default_admin()
    if "--seed" in sys.argv:
        seed_data()

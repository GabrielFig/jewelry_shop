import os

# Must be set before any app module is imported so unit_of_work.py builds
# its SQLAlchemy engine pointing at SQLite, not the Postgres instance.
os.environ.setdefault("DATABASE_URL", "sqlite:///./jewelry.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")

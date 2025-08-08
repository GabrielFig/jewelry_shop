from abc import ABC, abstractmethod
from app.adapters.repository import AbstractBatchRepository, InMemoryBatchRepository, SqlAlchemyBatchRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "sqlite:///./jewelry.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class AbstractUnitOfWork(ABC):
    batches : AbstractBatchRepository

    def __enter__(self) -> 'AbstractUnitOfWork':
        return self
    
    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.batches = InMemoryBatchRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self._session = SessionLocal()
        self.batches = SqlAlchemyBatchRepository(self._session)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self.committed:
            self.rollback()
        self._session.close()

    def commit(self):
        self._session.commit()
        self.committed = True

    def rollback(self):
        self._session.rollback()

from abc import ABC, abstractmethod
from app.adapters.repository import AbstractBatchRepository, InMemoryBatchRepository


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

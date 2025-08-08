from abc import ABC, abstractmethod
from typing import List
from app.domain.models import Batch


class AbstractBatchRepository(ABC):
    @abstractmethod
    def add(self, batch: Batch) -> None:
        pass

    @abstractmethod
    def get(self, ref: str) -> Batch:
        pass

    @abstractmethod
    def list(self) -> List[Batch]:
        pass


class InMemoryBatchRepository(AbstractBatchRepository):
    def __init__(self):
        self._batches = []

    def add(self, batch: Batch) -> None:
        self._batches.append(batch)

    def get(self, ref: str) -> Batch:
        return next(b for b in self._batches if b.ref == ref)

    def list(self) -> List[Batch]:
        return list(self._batches)
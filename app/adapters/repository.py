from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Batch
from sqlalchemy.orm import Session
from app.adapters.sqlalchemy_models import BatchModel


class AbstractBatchRepository(ABC):
    @abstractmethod
    def add(self, batch: Batch) -> None:
        pass

    @abstractmethod
    def get(self, ref: str) -> Optional[Batch]:
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


class SqlAlchemyBatchRepository(AbstractBatchRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, batch: Batch):
        model = BatchModel(
            reference=batch.ref,
            quantity=batch.purchased_quantity,
            sku=batch.sku
        )
        self._session.add(model)
    def get(self, ref: str) -> Optional[Batch]:
        model = self._session.query(BatchModel).filter_by(reference=ref).first()
        print (type(model))
        if model is None:
            return None
        return Batch(
            ref=str(model.reference),
            sku=str(model.sku),
            purchased_quantity=model.quantity  # ← nombre correcto según tu entidad # type: ignore
        )


    def list(self) -> List[Batch]:
        return [
            Batch(str(m.reference), str(m.sku),m.quantity) # type: ignore
            for m in self._session.query(BatchModel).all()
        ]
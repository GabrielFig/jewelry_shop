from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BatchModel(Base):
    __tablename__ = 'batches'

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference = Column(String(255), unique=True)
    sku = Column(String(255))
    quantity = Column(Integer, nullable=False)
    

from sqlalchemy.orm import sessionmaker
from app.adapters.sqlalchemy_models import BatchModel
from app.unit_of_work import engine

Session = sessionmaker(bind=engine)
session = Session()

session.add(BatchModel(reference="batch-001", sku="GOLD_RING", quantity=10))
session.commit()

batch = session.query(BatchModel).first()
if batch is not None:
	print(batch.reference, batch.sku, batch.quantity)
else:
	print("No batch found.")
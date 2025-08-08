from app.adapters.sqlalchemy_models import Base
from app.unit_of_work import engine

Base.metadata.create_all(bind=engine)

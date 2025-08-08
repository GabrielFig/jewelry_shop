from fastapi import FastAPI
from app.entrypoints.api import router


app = FastAPI(title="Jewelry Shop API", version="1.0.0")
app.include_router(router)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.entrypoints.api import router

app = FastAPI(
    title="E-Commerce Platform API",
    description=(
        "A domain-driven e-commerce backend built with Clean Architecture, "
        "Repository Pattern, Unit of Work, and Strategy Pattern for payments. "
        "Configured as a jewelry shop — adaptable to any product domain."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

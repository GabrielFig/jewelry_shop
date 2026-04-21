import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.dependencies import get_current_user, require_admin
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.domain.models import User, UserRole
from app.limiter import limiter
from app.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthOut, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterIn):
    with SqlAlchemyUnitOfWork() as uow:
        if uow.users.get_by_email(body.email):
            raise HTTPException(status_code=400, detail="Registration failed")
        user = User(
            id=str(uuid.uuid4()),
            email=body.email,
            hashed_password=hash_password(body.password),
            name=body.name,
            role=UserRole.CUSTOMER,
        )
        uow.users.add(user)
        uow.commit()

    token = create_access_token(subject=user.id, role=user.role.value)
    return AuthOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value),
    )


@router.post("/login", response_model=AuthOut)
@limiter.limit("10/minute")
def login(request: Request, body: LoginIn):
    with SqlAlchemyUnitOfWork() as uow:
        user = uow.users.get_by_email(body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        logger.warning("Failed login attempt for email: %s from %s", body.email, request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token(subject=user.id, role=user.role.value)
    return AuthOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
    )


@router.post("/admin/create", response_model=AuthOut, status_code=201)
def create_admin(body: RegisterIn, _: User = Depends(require_admin)):
    """Create an admin user. Requires an existing admin account."""
    with SqlAlchemyUnitOfWork() as uow:
        if uow.users.get_by_email(body.email):
            raise HTTPException(status_code=400, detail="Registration failed")
        user = User(
            id=str(uuid.uuid4()),
            email=body.email,
            hashed_password=hash_password(body.password),
            name=body.name,
            role=UserRole.ADMIN,
        )
        uow.users.add(user)
        uow.commit()

    token = create_access_token(subject=user.id, role=user.role.value)
    return AuthOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value),
    )

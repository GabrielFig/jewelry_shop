import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set")
    return secret


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises InvalidTokenError if the token is invalid or expired."""
    return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])

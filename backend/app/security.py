"""JWT creation/verification and the dependencies that protect endpoints."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.responses import AppError

# Dev fallback only. Production must set JWT_SECRET (32+ random bytes) or anyone can forge tokens.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret-change-me-in-env")
ALGORITHM = "HS256"
TOKEN_TTL = {"access": timedelta(minutes=30), "refresh": timedelta(days=30)}

bearer = HTTPBearer(auto_error=False)


def create_token(user_id: uuid.UUID, kind: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": kind, "iat": now, "exp": now + TOKEN_TTL[kind]}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def token_pair(user_id: uuid.UUID) -> dict:
    return {
        "access_token": create_token(user_id, "access"),
        "refresh_token": create_token(user_id, "refresh"),
        "token_type": "bearer",
    }


def decode_token(token: str, expected_type: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "Oturum süresi doldu")
    except jwt.InvalidTokenError:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi")
    # Stops a long-lived refresh token from being used as an access token, and vice versa.
    if payload.get("type") != expected_type:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi")
    return uuid.UUID(payload["sub"])


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise AppError(401, "UNAUTHORIZED", "Bu işlem için giriş yapmalısınız")
    user = db.get(User, decode_token(creds.credentials, "access"))
    if user is None:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi")
    return user


def require_roles(*roles: Role):
    """Role comes from the database, not the token, so a role change applies immediately."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(403, "FORBIDDEN", "Bu işlem için yetkiniz yok")
        return user

    return checker

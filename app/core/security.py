"""
Security utilities: bcrypt password hashing and JWT token management.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Bcrypt password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate encoded JWT access token with expiration."""
    to_encode: Dict[str, Any] = {}
    for key, val in data.items():
        if isinstance(val, uuid.UUID):
            to_encode[key] = str(val)
        else:
            to_encode[key] = val

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


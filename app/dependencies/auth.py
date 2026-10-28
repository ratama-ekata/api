"""
Authentication and Role-Based Access Control (RBAC) dependencies.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenData
from app.services.user_service import UserService

# OAuth2 password bearer flow pointing to the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that decodes JWT bearer token and retrieves
    the authenticated User strictly using SQLAlchemy ORM.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        username: Optional[str] = payload.get("username")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role, username=username)
    except JWTError:
        raise credentials_exception

    user = UserService.get_by_email(db, token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user


def require_roles(*allowed_roles: UserRole):
    """
    Factory for role-based authorization dependencies.

    Args:
        *allowed_roles (UserRole): Roles permitted to access the endpoint.

    Returns:
        Callable: Dependency returning the authenticated user if authorized.
    """
    role_values = [r.value for r in allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {role_values}",
            )
        return current_user

    return role_checker


# Reusable preconfigured role dependencies
require_system_admin = require_roles(UserRole.SYSTEM_ADMIN)
require_admin_or_system_admin = require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN)

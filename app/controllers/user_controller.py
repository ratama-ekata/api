"""
User and authentication controller endpoints with Role-Based Access Control (RBAC).
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserAdminCreate,
    UserLogin,
    UserResponse,
    Token,
)
from app.services.user_service import UserService
from app.dependencies.auth import (
    get_current_user,
    require_system_admin,
    require_admin_or_system_admin,
)

router = APIRouter(prefix="/users", tags=["Users & Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Role: USER)",
    description="Public registration endpoint. All accounts registered here are assigned the USER role.",
)
def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user account with unique username, email, phone number, and password."""
    return UserService.create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and obtain JWT token (OAuth2 Form)",
    description="OAuth2 standard login endpoint. Enter either username or email in the username field.",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible login:
    Accepts application/x-www-form-urlencoded credentials.
    In the `username` field, pass the user's username or email address.
    """
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": str(user.id),
            "role": user.role,
            "username": user.username,
        }
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.post(
    "/login/json",
    response_model=Token,
    summary="Authenticate user and obtain JWT token (JSON Payload)",
    description="Convenient JSON login endpoint for frontend and mobile applications.",
)
def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """JSON-based login endpoint accepting either email or username."""
    user = UserService.authenticate_user(
        db, credentials.username_or_email, credentials.password
    )
    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": str(user.id),
            "role": user.role,
            "username": user.username,
        }
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the currently authenticated user."""
    return current_user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users (ADMIN & SYSTEM_ADMIN only)",
    description="Retrieve all user accounts in the system. Accessible by ADMIN and SYSTEM_ADMIN roles.",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """List registered users with pagination."""
    return UserService.list_all_users(db, skip=skip, limit=limit)


@router.post(
    "/admin/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user with specific role (SYSTEM_ADMIN only)",
    description="Create an account with explicit role assignment (SYSTEM_ADMIN, ADMIN, USER). Admin role cannot use this endpoint.",
)
def create_user_by_system_admin(
    user_in: UserAdminCreate,
    current_user: User = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """Restricted to SYSTEM_ADMIN: create users and assign roles."""
    return UserService.create_user_by_admin(db, user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (SYSTEM_ADMIN only)",
    description="Permanently delete a user account. Restricted strictly to SYSTEM_ADMIN; ADMIN role cannot delete users.",
)
def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """Restricted to SYSTEM_ADMIN: delete users by primary key."""
    UserService.delete_user(db, user_id=user_id, requesting_user=current_user)
    return None

"""
Pydantic schemas for user registration, authentication, tokens, and profiles.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for shared user attributes."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
        description="Unique username containing letters, numbers, underscores, dots, or dashes",
    )
    email: EmailStr = Field(..., description="Valid user email address")
    phone_no: Optional[str] = Field(
        None,
        max_length=25,
        description="User contact phone number (e.g. +94771234567)",
    )


class UserCreate(UserBase):
    """
    Schema for public user registration.
    Always registers as role 'USER'.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password with min 8 and max 128 characters",
    )


class UserAdminCreate(UserCreate):
    """
    Schema for user creation by SYSTEM_ADMIN.
    Allows assigning explicit roles (SYSTEM_ADMIN, ADMIN, USER).
    """
    role: UserRole = Field(
        default=UserRole.USER,
        description="User authorization role (SYSTEM_ADMIN, ADMIN, USER)",
    )


class UserLogin(BaseModel):
    """Schema for direct JSON-based login with either email or username."""
    username_or_email: str = Field(
        ...,
        description="User's username or email address",
    )
    password: str = Field(..., description="User's plain password")


class UserResponse(UserBase):
    """Schema for serialized user profiles (excludes sensitive fields like hashed_password)."""
    id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT bearer token response."""
    access_token: str = Field(..., description="JWT bearer access token")
    token_type: str = Field("bearer", description="Token type, defaults to bearer")
    role: str = Field(..., description="Role of the authenticated user")
    username: str = Field(..., description="Username of the authenticated user")


class TokenData(BaseModel):
    """Schema for decoded JWT token payload data."""
    email: Optional[str] = None
    role: Optional[str] = None
    username: Optional[str] = None

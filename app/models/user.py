"""
User ORM model representing registered users with role-based access control (RBAC).
"""

import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    User roles enum:
    - SYSTEM_ADMIN: Full administrative capabilities (user creation, deletion, role assignments, system management).
    - ADMIN: Administrative capabilities except adding or deleting users.
    - USER: Standard citizen/consumer permissions.
    """
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    """
    SQLAlchemy ORM model representing application users.

    Attributes:
        id (int): Primary key identifier.
        username (str): Unique username for identification/login.
        email (str): Unique, indexed email address for identification/login.
        phone_no (str): Contact phone number.
        hashed_password (str): Securely hashed user password.
        role (str): User authorization role (SYSTEM_ADMIN, ADMIN, USER).
        is_active (bool): Flag indicating if user account is active.
        created_at (datetime): Timestamp when record was created.
        updated_at (datetime): Timestamp when record was last updated.
        uploads (relationship): Relationship to files uploaded by this user.
    """
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_no = Column(String(25), index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default=UserRole.USER.value, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # One-to-many relationship with uploaded files
    uploads = relationship("UploadedFile", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"

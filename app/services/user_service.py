"""
User business service: handles user registration, authentication, RBAC,
and startup database seeding strictly using SQLAlchemy ORM.
"""

import logging
import uuid
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserAdminCreate

logger = logging.getLogger("ratamaekata_api.user_service")


class UserService:
    """Service class for user management and RBAC operations."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch user by email strictly using SQLAlchemy ORM."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """Fetch user by username strictly using SQLAlchemy ORM."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_identifier(db: Session, identifier: str) -> Optional[User]:
        """Fetch user by either username or email strictly using SQLAlchemy ORM."""
        return db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key ID strictly using SQLAlchemy ORM."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def list_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination strictly using SQLAlchemy ORM."""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """
        Public user registration:
        - Validates uniqueness of email and username.
        - Automatically assigns role 'USER'.
        """
        if UserService.get_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        if UserService.get_by_username(db, user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            phone_no=user_in.phone_no,
            hashed_password=hashed_password,
            role=UserRole.USER.value,  # Public signups are strictly USER role
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("New public user registered: %s (id: %s)", new_user.username, new_user.id)
        return new_user

    @staticmethod
    def create_user_by_admin(db: Session, user_in: UserAdminCreate) -> User:
        """
        Create a user with an assigned role (SYSTEM_ADMIN, ADMIN, USER).
        Strictly restricted to SYSTEM_ADMIN callers.
        """
        if UserService.get_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        if UserService.get_by_username(db, user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            phone_no=user_in.phone_no,
            hashed_password=hashed_password,
            role=user_in.role.value,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(
            "User created by SYSTEM_ADMIN: %s (role: %s, id: %s)",
            new_user.username,
            new_user.role,
            new_user.id,
        )
        return new_user

    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID, requesting_user: User) -> None:
        """
        Delete a user record strictly using SQLAlchemy ORM.
        Restricted to SYSTEM_ADMIN.
        """
        target_user = UserService.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if target_user.id == requesting_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SYSTEM_ADMIN cannot delete their own account.",
            )

        db.delete(target_user)
        db.commit()
        logger.info("User deleted by SYSTEM_ADMIN: %s (id: %s)", target_user.username, user_id)

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> User:
        """Verify user credentials by email or username and ensure account is active."""
        user = UserService.get_by_identifier(db, identifier)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account",
            )

        return user

    @staticmethod
    def seed_initial_users(db: Session) -> None:
        """
        Automatically seed the initial SYSTEM_ADMIN and ADMIN accounts on startup
        if they do not already exist in the PostgreSQL database.
        """
        # 1. Seed SYSTEM_ADMIN
        existing_sysadmin = db.query(User).filter(
            or_(
                User.email == settings.SYSADMIN_EMAIL,
                User.username == settings.SYSADMIN_USERNAME,
                User.role == UserRole.SYSTEM_ADMIN.value,
            )
        ).first()

        if not existing_sysadmin:
            sysadmin = User(
                username=settings.SYSADMIN_USERNAME,
                email=settings.SYSADMIN_EMAIL,
                phone_no=settings.SYSADMIN_PHONE,
                hashed_password=get_password_hash(settings.SYSADMIN_PASSWORD),
                role=UserRole.SYSTEM_ADMIN.value,
                is_active=True,
            )
            db.add(sysadmin)
            db.commit()
            logger.info("Successfully seeded default SYSTEM_ADMIN account: %s", settings.SYSADMIN_EMAIL)
        else:
            logger.info("SYSTEM_ADMIN account already verified in database.")

        # 2. Seed ADMIN
        existing_admin = db.query(User).filter(
            or_(
                User.email == settings.ADMIN_EMAIL,
                User.username == settings.ADMIN_USERNAME,
            )
        ).first()

        if not existing_admin:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                phone_no=settings.ADMIN_PHONE,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Successfully seeded default ADMIN account: %s", settings.ADMIN_EMAIL)
        else:
            logger.info("ADMIN account already verified in database.")

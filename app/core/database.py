"""
Database connection, engine instantiation, sessionmaker, and session dependency.
Strictly relies on SQLAlchemy ORM.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Create SQLAlchemy engine with pool_pre_ping for connection health verification
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Thread-local sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative Base for SQLAlchemy ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a clean database session per request,
    guaranteeing closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


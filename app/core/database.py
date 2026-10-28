"""
Database connection, engine instantiation, sessionmaker, and session dependency.
Strictly relies on SQLAlchemy ORM.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Handle postgres:// vs postgresql:// (common in Neon/Supabase connection URIs)
raw_db_url = settings.DATABASE_URL
if raw_db_url and raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

# Set short connection timeout so serverless function cold starts do not hang on unreachable DB
connect_args = {"connect_timeout": 5} if "postgresql" in raw_db_url else {}

# Create SQLAlchemy engine with pool_pre_ping for connection health verification
engine = create_engine(
    raw_db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
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


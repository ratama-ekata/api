"""
Central application configuration loaded from environment variables (.env).
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file at project root
load_dotenv()


def _safe_int(val: Optional[str], default: int) -> int:
    """Safely parse integer from environment variable string."""
    try:
        return int(val) if val is not None and str(val).strip() else default
    except (ValueError, TypeError):
        return default


class Settings:
    """Application runtime settings and environment variables."""

    # Project metadata
    PROJECT_NAME: str = "Ratamaekata API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = ""

    # PostgreSQL Database Connection URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ratamaekata_db",
    )

    # JWT Authentication & Cryptography
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "9a4b8c1d3e5f7a2b6c8d0e1f3a5b7c9d2e4f6a8b0c2d4e6f8a1b3c5d7e9f0a2b",
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _safe_int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), 60)

    # Initial System Admin Seed Credentials
    SYSADMIN_USERNAME: str = os.getenv("SYSADMIN_USERNAME", "sysadmin")
    SYSADMIN_EMAIL: str = os.getenv("SYSADMIN_EMAIL", "sysadmin@ratamaekata.gov.lk")
    SYSADMIN_PASSWORD: str = os.getenv("SYSADMIN_PASSWORD", "SysAdmin@2026!")
    SYSADMIN_PHONE: str = os.getenv("SYSADMIN_PHONE", "+94770000001")

    # Initial Admin Seed Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@ratamaekata.gov.lk")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@2026!")
    ADMIN_PHONE: str = os.getenv("ADMIN_PHONE", "+94770000002")

    # AWS S3 Cloud Storage Credentials
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET_NAME: str = os.getenv("AWS_S3_BUCKET_NAME", "ratamaekata-uploads")
    AWS_S3_CUSTOM_DOMAIN: str = os.getenv("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL", "")

    # SMTP Email Notification Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = _safe_int(os.getenv("SMTP_PORT"), 587)
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() in ("true", "1", "yes")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@ratamaekata.gov.lk")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "රටම එකට - Ratamaekata.gov.lk")


settings = Settings()

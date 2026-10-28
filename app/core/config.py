
"""
Central application configuration loaded from environment variables (.env).
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()


def _safe_int(val: Optional[str], default: int) -> int:
    """Safely parse integer from environment variable string."""
    try:
        return int(val) if val is not None and str(val).strip() else default
    except (ValueError, TypeError):
        return default


def _env(name: str, default: str = "") -> str:
    """Read an environment variable and remove surrounding quotes."""
    return os.getenv(name, default).strip("\"'")


class Settings:
    """Application runtime settings and environment variables."""

    # Project metadata
    PROJECT_NAME: str = "Ratamaekata API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = ""

    # PostgreSQL Database Connection URL
    DATABASE_URL: str = _env("DATABASE_URL")

    # JWT Authentication & Cryptography
    SECRET_KEY: str = _env("SECRET_KEY")
    ALGORITHM: str = _env("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _safe_int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), 60
    )

    # Initial System Admin Seed Credentials
    SYSADMIN_USERNAME: str = _env("SYSADMIN_USERNAME", "sysadmin")
    SYSADMIN_EMAIL: str = _env(
        "SYSADMIN_EMAIL", "sysadmin@ratamaekata.gov.lk"
    )
    SYSADMIN_PASSWORD: str = _env("SYSADMIN_PASSWORD")
    SYSADMIN_PHONE: str = _env("SYSADMIN_PHONE", "+94770000001")

    # Initial Admin Seed Credentials
    ADMIN_USERNAME: str = _env("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = _env(
        "ADMIN_EMAIL", "admin@ratamaekata.gov.lk"
    )
    ADMIN_PASSWORD: str = _env("ADMIN_PASSWORD")
    ADMIN_PHONE: str = _env("ADMIN_PHONE", "+94770000002")

    # AWS S3 Cloud Storage Credentials
    AWS_ACCESS_KEY_ID: str = _env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = _env("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = _env("AWS_REGION", "ap-south-1")
    AWS_S3_BUCKET_NAME: str = _env(
        "AWS_S3_BUCKET_NAME", "lms-testing-bucket-halcyon"
    )
    AWS_S3_CUSTOM_DOMAIN: str = _env("AWS_S3_CUSTOM_DOMAIN")
    AWS_ENDPOINT_URL: str = _env("AWS_ENDPOINT_URL")

    # SMTP Email Notification Settings
    SMTP_HOST: str = _env("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = _safe_int(os.getenv("SMTP_PORT"), 587)
    SMTP_USER: str = _env("SMTP_USER")
    SMTP_PASSWORD: str = _env("SMTP_PASSWORD")
    SMTP_TLS: bool = _env("SMTP_TLS", "True").lower() in (
        "true", "1", "yes"
    )
    SMTP_FROM_EMAIL: str = _env(
        "SMTP_FROM_EMAIL", "noreply@ratamaekata.gov.lk"
    )
    SMTP_FROM_NAME: str = _env(
        "SMTP_FROM_NAME", "රටම එකට - Ratamaekata.gov.lk"
    )


settings = Settings()

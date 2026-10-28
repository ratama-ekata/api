"""
Models package: registers all SQLAlchemy ORM database models.
"""

from app.core.database import Base
from app.models.user import User, UserRole
from app.models.upload import UploadedFile
from app.models.suspect_report import SuspectReport, SuspectReportFile

__all__ = [
    "Base",
    "User",
    "UserRole",
    "UploadedFile",
    "SuspectReport",
    "SuspectReportFile",
]

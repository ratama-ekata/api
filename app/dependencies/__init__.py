"""
Dependencies package: re-exports reusable FastAPI dependencies.
"""

from app.core.database import get_db
from app.dependencies.auth import (
    get_current_user,
    oauth2_scheme,
    require_roles,
    require_system_admin,
    require_admin_or_system_admin,
)

__all__ = [
    "get_db",
    "get_current_user",
    "oauth2_scheme",
    "require_roles",
    "require_system_admin",
    "require_admin_or_system_admin",
]

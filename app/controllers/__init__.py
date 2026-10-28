"""
Controllers package: aggregates all route controllers into a central API router.
"""

from fastapi import APIRouter
from app.controllers.user_controller import router as user_router
from app.controllers.upload_controller import router as upload_router
from app.controllers.suspect_report_controller import router as suspect_report_router

# Central API router combining all domain controllers
api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(upload_router)
api_router.include_router(suspect_report_router)

__all__ = [
    "api_router",
    "user_router",
    "upload_router",
    "suspect_report_router",
]

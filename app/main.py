"""
Main entry point for the FastAPI application.
Initializes FastAPI, configures CORS middleware, executes database table creation,
auto-seeds initial administrative users, and registers domain controllers.
"""

import logging
import os
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request, Depends, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, get_db
import app.models  # Ensures all ORM models are registered with Base.metadata
from app.services.user_service import UserService
from app.services.suspect_report_service import SuspectReportService
from app.controllers import api_router
from app.controllers.suspect_report_controller import submit_suspect_report_json
from app.schemas.suspect_report import SuspectReportCreate, SuspectReportResponse

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("ratamaekata_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    1. Verifies/creates database tables using SQLAlchemy Base.metadata.create_all().
    2. Automatically seeds default SYSTEM_ADMIN and ADMIN accounts if they do not exist.
    """
    logger.info("Initializing application startup sequence...")
    is_localhost_db = "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL
    if os.getenv("VERCEL") and is_localhost_db:
        logger.warning(
            "DATABASE_URL is set to localhost on Vercel! "
            "Please configure your cloud PostgreSQL database (e.g. Neon, Supabase) in Vercel Environment Variables. "
            "Skipping startup table initialization to avoid serverless function timeouts."
        )
    else:
        try:
            # Create database tables strictly using SQLAlchemy ORM metadata
            logger.info("Creating database tables using SQLAlchemy Base.metadata.create_all()...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")

            # Ensure report_id column exists if table was previously created
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE suspect_reports ADD COLUMN IF NOT EXISTS report_id VARCHAR(50);"))
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_suspect_reports_report_id ON suspect_reports (report_id);"))
                    conn.commit()
            except Exception as mig_exc:
                logger.debug("Migration check completed: %s", mig_exc)

            # Automatically seed initial SYSTEM_ADMIN and ADMIN accounts
            logger.info("Checking and seeding default administrative accounts...")
            with SessionLocal() as db:
                UserService.seed_initial_users(db)

        except Exception as exc:
            logger.error(
                "Database startup initialization error: %s. "
                "Please ensure PostgreSQL is running and DATABASE_URL is correctly configured.",
                exc,
            )
    yield
    logger.info("Application shutdown completed.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-ready FastAPI backend for api.ratamaekata.gov.lk. "
        "Architected with Clean Layered Architecture: Core, Models, Schemas, "
        "Services, Controllers, and Dependencies. "
        "Features RBAC: SYSTEM_ADMIN, ADMIN, and USER."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Middleware
# Whitelist localhost, Vercel deployments (*.vercel.app), and production domain
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|([a-zA-Z0-9_-]+\.)*vercel\.app|([a-zA-Z0-9_-]+\.)*ratamaekata\.gov\.lk)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def vercel_path_rewrite_middleware(request: Request, call_next):
    """
    Normalizes path in Vercel Serverless environment:
    Strips internal serverless prefixes like /api/index.py or /api/index
    so that FastAPI router matches user-intended paths.
    """
    path = request.scope.get("path", "")
    for prefix in ("/api/index.py", "/api/index", "/index.py"):
        if path.startswith(prefix):
            new_path = path[len(prefix):]
            request.scope["path"] = new_path if new_path.startswith("/") else f"/{new_path}"
            break
    return await call_next(request)

# Mount all domain controllers via central API router (with and without /api prefix)
app.include_router(api_router)
app.include_router(api_router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler ensuring proper JSON and CORS headers on internal errors."""
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Database or internal server error: {str(exc)}"},
    )


@app.get(
    "/",
    tags=["Root & Health"],
    summary="API Root & Status",
    response_class=JSONResponse,
)
@app.get(
    "/api",
    tags=["Root & Health"],
    include_in_schema=False,
    response_class=JSONResponse,
)
@app.get(
    "/api/data",
    tags=["Root & Health"],
    include_in_schema=False,
    response_class=JSONResponse,
)
def root():
    """Root health verification endpoint."""
    return {
        "status": "healthy",
        "service": "api.ratamaekata.gov.lk",
        "version": settings.VERSION,
        "docs": "/docs",
        "message": "Welcome to the Ratamaekata API backend service.",
    }


@app.get(
    "/health",
    tags=["Root & Health"],
    summary="Detailed Health Check",
    status_code=status.HTTP_200_OK,
)
@app.get(
    "/api/health",
    tags=["Root & Health"],
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
def health_check():
    """Database connectivity health check."""
    db_status = "connected"
    try:
        with engine.connect() as connection:
            connection.execute(app.models.User.__table__.select().limit(1))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "online",
        "database": db_status,
        "service": "api.ratamaekata.gov.lk",
    }


@app.get("/api/docs", include_in_schema=False)
def redirect_api_docs():
    """Redirect /api/docs to Swagger UI."""
    return RedirectResponse(url="/docs")


@app.post(
    "/reports",
    tags=["Reports"],
    summary="Submit report alias (Public)",
    status_code=status.HTTP_201_CREATED,
    response_model=SuspectReportResponse,
)
@app.post(
    "/api/reports",
    tags=["Reports"],
    include_in_schema=False,
    status_code=status.HTTP_201_CREATED,
    response_model=SuspectReportResponse,
)
async def submit_reports_alias(
    request: Request,
    db: Session = Depends(get_db),
):
    """Direct alias endpoint supporting both multipart/form-data (with file uploads) and JSON."""
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()

        fullname = str(form.get("fullname") or form.get("fullName") or "").strip()
        mobile = str(form.get("mobile") or form.get("phone") or "").strip()
        police_station = str(form.get("police_station") or form.get("policeStation") or "").strip()
        type_of_activity = str(form.get("type_of_activity") or form.get("activityType") or "Other").strip()
        activity_description = str(form.get("activity_description") or form.get("description") or "").strip()
        email = str(form.get("email") or "not_provided@ratamaekata.gov.lk").strip()
        nic = str(form.get("nic") or "NOT_PROVIDED").strip()
        address = str(form.get("address") or "Not provided").strip()

        # Extract files: can be list under "files", "files[]", "attachments"
        files: List[UploadFile] = []
        for key in ("files", "files[]", "attachments"):
            file_items = form.getlist(key)
            for item in file_items:
                if isinstance(item, UploadFile) and item.filename:
                    files.append(item)

        # Also collect any UploadFile value not yet included
        for val in form.values():
            if isinstance(val, UploadFile) and val.filename and val not in files:
                files.append(val)

        report = await SuspectReportService.create_report(
            db=db,
            fullname=fullname,
            email=email,
            mobile=mobile,
            nic=nic,
            address=address,
            police_station=police_station,
            type_of_activity=type_of_activity,
            activity_description=activity_description,
            files=files if files else None,
        )
    else:
        # JSON payload
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON or multipart request body")
        report_in = SuspectReportCreate(**body)
        return await submit_suspect_report_json(report_in=report_in, db=db)

    report_dict = SuspectReportResponse.model_validate(report).model_dump()
    report_dict["report_id"] = report.report_id
    report_dict["referenceNumber"] = report.report_id or f"RE-{report.created_at.year if report.created_at else 2026}-{str(report.id)[:5].upper()}"
    return report_dict


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

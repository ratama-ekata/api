"""
Suspect report controller: handles public citizen incident reporting
with multiple evidence files (images, zip archives, docs) uploaded to AWS S3,
and provides protected viewing endpoints for ADMIN and SYSTEM_ADMIN roles.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.suspect_report import SuspectReportResponse, SuspectReportCreate
from app.services.suspect_report_service import SuspectReportService
from app.dependencies.auth import (
    require_admin_or_system_admin,
    require_system_admin,
)

router = APIRouter(prefix="/suspect-reports", tags=["Suspect Reports"])


@router.post(
    "/",
    response_model=SuspectReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit suspect incident report (Public - No Auth Required)",
    description=(
        "Public endpoint allowing citizens to report suspicious activity. "
        "Supports multiple optional evidence files (images, zip files, documents) which are "
        "streamed directly to AWS S3 and their public links saved in PostgreSQL."
    ),
)
@router.post(
    "",
    include_in_schema=False,
    response_model=SuspectReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_suspect_report(
    fullname: str = Form(..., min_length=2, max_length=255, description="Citizen full name"),
    email: Optional[str] = Form(None, description="Contact email address"),
    mobile: str = Form(..., min_length=6, max_length=30, description="Contact mobile phone number"),
    nic: Optional[str] = Form(None, description="National Identity Card number"),
    address: Optional[str] = Form(None, description="Citizen / incident address"),
    police_station: str = Form(..., min_length=2, max_length=150, description="Designated police station"),
    type_of_activity: str = Form(..., min_length=2, max_length=150, description="Type/category of suspicious activity"),
    activity_description: str = Form(..., min_length=5, description="Detailed description of the event"),
    files: Optional[List[UploadFile]] = File(
        None,
        description="Multiple evidence files (images, zip files, documents) uploaded directly to AWS S3",
    ),
    db: Session = Depends(get_db),
):
    """
    Public report submission handler:
    - No authentication required.
    - Uploads attached evidence files directly to AWS S3 if provided.
    - Saves S3 links and metadata in PostgreSQL database.
    """
    final_email = (email or "not_provided@ratamaekata.gov.lk").strip()
    final_nic = (nic or "NOT_PROVIDED").strip()
    final_address = (address or "Not provided").strip()

    report = await SuspectReportService.create_report(
        db=db,
        fullname=fullname,
        email=final_email,
        mobile=mobile,
        nic=final_nic,
        address=final_address,
        police_station=police_station,
        type_of_activity=type_of_activity,
        activity_description=activity_description,
        files=files,
    )
    report_dict = SuspectReportResponse.model_validate(report).model_dump()
    report_dict["report_id"] = report.report_id
    report_dict["referenceNumber"] = report.report_id or f"RE-{report.created_at.year if report.created_at else 2026}-{str(report.id)[:5].upper()}"
    return report_dict


@router.post(
    "/json",
    response_model=SuspectReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit suspect incident report via JSON (Public - No Auth Required)",
    description="Allows public report submission using JSON payload without file attachments.",
)
async def submit_suspect_report_json(
    report_in: SuspectReportCreate,
    db: Session = Depends(get_db),
):
    fullname = report_in.get_fullname()
    mobile = report_in.get_mobile()
    police_station = report_in.get_police_station()
    activity_description = report_in.get_activity_description()

    if not fullname:
        raise HTTPException(status_code=400, detail="Full name is required")
    if not mobile:
        raise HTTPException(status_code=400, detail="Mobile phone number is required")
    if not police_station:
        raise HTTPException(status_code=400, detail="Police station is required")
    if not activity_description:
        raise HTTPException(status_code=400, detail="Activity description is required")

    report = await SuspectReportService.create_report(
        db=db,
        fullname=fullname,
        email=report_in.get_email(),
        mobile=mobile,
        nic=report_in.get_nic(),
        address=report_in.get_address(),
        police_station=police_station,
        type_of_activity=report_in.get_type_of_activity(),
        activity_description=activity_description,
        files=None,
    )
    report_dict = SuspectReportResponse.model_validate(report).model_dump()
    report_dict["report_id"] = report.report_id
    report_dict["referenceNumber"] = report.report_id or f"RE-{report.created_at.year if report.created_at else 2026}-{str(report.id)[:5].upper()}"
    return report_dict


@router.get(
    "",
    response_model=List[SuspectReportResponse],
    include_in_schema=False,
)
@router.get(
    "/",
    response_model=List[SuspectReportResponse],
    summary="List all suspect reports (ADMIN & SYSTEM_ADMIN only)",
    description=(
        "Retrieve all submitted suspect incident reports including attached S3 evidence links. "
        "Restricted strictly to authenticated ADMIN and SYSTEM_ADMIN roles."
    ),
)
def list_suspect_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    police_station: Optional[str] = Query(None, description="Filter by police station"),
    type_of_activity: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: User = Depends(require_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """
    Protected endpoint:
    Only ADMIN and SYSTEM_ADMIN can view suspect reports.
    """
    return SuspectReportService.list_reports(
        db=db,
        skip=skip,
        limit=limit,
        police_station=police_station,
        type_of_activity=type_of_activity,
    )


@router.get(
    "/{report_id}",
    response_model=SuspectReportResponse,
    summary="Get single suspect report by ID (ADMIN & SYSTEM_ADMIN only)",
    description=(
        "Retrieve complete details of a specific suspect report and all its S3 evidence links. "
        "Accepts either database UUID or official Report ID (e.g. RE-2026-A9019B). "
        "Restricted strictly to ADMIN and SYSTEM_ADMIN roles."
    ),
)
@router.get(
    "/{report_id}/",
    response_model=SuspectReportResponse,
    include_in_schema=False,
)
def get_suspect_report_by_id(
    report_id: str,
    current_user: User = Depends(require_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """
    Protected endpoint:
    Retrieve single report by UUID or report_id. Restricted to ADMIN and SYSTEM_ADMIN.
    """
    report = SuspectReportService.get_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suspect report '{report_id}' not found",
        )
    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a suspect report and its S3 files (SYSTEM_ADMIN only)",
    description=(
        "Permanently delete a suspect report from the database and remove all its "
        "evidence files from AWS S3. Restricted strictly to SYSTEM_ADMIN."
    ),
)
def delete_suspect_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """
    Protected endpoint:
    Delete report and all associated S3 objects. Restricted strictly to SYSTEM_ADMIN.
    """
    SuspectReportService.delete_report(db, report_id)
    return None


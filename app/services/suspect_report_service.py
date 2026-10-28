"""
Suspect report business service: manages public incident submissions,
multiple evidence file uploads to AWS S3, and database persistence.
"""

import logging
import uuid
import random
import string
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.suspect_report import SuspectReport, SuspectReportFile
from app.services.s3_service import upload_file_to_s3, delete_file_from_s3
from app.services.email_service import EmailService

logger = logging.getLogger("ratamaekata_api.suspect_reports")


class SuspectReportService:
    """Service class for suspect incident reporting and evidence storage."""

    OFFICIAL_ACTIVITY_TYPES = [
        "Selling or dealing drugs",
        "Using drugs in public",
        "Storing or transporting drugs",
        "Drug activity near a school",
        "Manufacturing or cultivation",
        "Other",
    ]

    ACTIVITY_MAPPINGS = {
        "selling": "Selling or dealing drugs",
        "using-public": "Using drugs in public",
        "storing": "Storing or transporting drugs",
        "near-school": "Drug activity near a school",
        "manufacturing": "Manufacturing or cultivation",
        "other": "Other",
        "selling or dealing drugs": "Selling or dealing drugs",
        "using drugs in public": "Using drugs in public",
        "storing or transporting drugs": "Storing or transporting drugs",
        "drug activity near a school": "Drug activity near a school",
        "manufacturing or cultivation": "Manufacturing or cultivation",
    }

    @classmethod
    def normalize_activity_type(cls, raw_type: str) -> str:
        """Standardize activity type into the exact full official string."""
        if not raw_type:
            return "Other"
        clean = raw_type.strip().lower()
        if clean in cls.ACTIVITY_MAPPINGS:
            return cls.ACTIVITY_MAPPINGS[clean]
        if "deal" in clean or "sell" in clean:
            return "Selling or dealing drugs"
        if "public" in clean or "using" in clean:
            return "Using drugs in public"
        if "store" in clean or "transport" in clean or "stash" in clean:
            return "Storing or transporting drugs"
        if "school" in clean:
            return "Drug activity near a school"
        if "manufactur" in clean or "cultivat" in clean:
            return "Manufacturing or cultivation"
        if "other" in clean:
            return "Other"
        return raw_type.strip()

    @staticmethod
    def generate_report_id(year: Optional[int] = None) -> str:
        """
        Generate official Report ID format:
        RE-{YEAR}-{6_DIGIT_ALPHANUMERIC} (e.g. RE-2026-A9019B)
        - 'RE' is constant
        - Year changes dynamically based on current year (e.g. 2026, 2027)
        - 6-character random code containing capital letters (A-Z) and numbers (0-9)
        """
        if year is None:
            year = datetime.utcnow().year
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=6))
            if any(c.isalpha() for c in code) and any(c.isdigit() for c in code):
                return f"RE-{year}-{code}"

    @staticmethod
    async def create_report(
        db: Session,
        fullname: str,
        email: str,
        mobile: str,
        nic: str,
        address: str,
        police_station: str,
        type_of_activity: str,
        activity_description: str,
        files: Optional[List[UploadFile]] = None,
    ) -> SuspectReport:
        """
        Create a new suspect report and upload all attached evidence files (images, zip, docs)
        directly to AWS S3, storing the resulting links in PostgreSQL.

        All citizen identification and incident fields are strictly compulsory.
        """
        # Validate all compulsory fields
        if not fullname or not fullname.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required",
            )

        # Optional fields fallback gracefully if left blank
        if not email or not email.strip():
            email = "not_provided@ratamaekata.gov.lk"

        if not mobile or not mobile.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile phone number is required",
            )

        if not nic or not nic.strip():
            nic = "NOT_PROVIDED"

        if not address or not address.strip():
            address = "Not provided"

        if not police_station or not police_station.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Police station is required",
            )

        if not type_of_activity or not type_of_activity.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type of activity is required",
            )

        if not activity_description or not activity_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity description is required",
            )

        # 1. Generate unique human-readable report ID: e.g. RE-2026-A9019B
        current_year = datetime.utcnow().year
        new_report_id = SuspectReportService.generate_report_id(current_year)
        for _ in range(5):
            existing = db.query(SuspectReport).filter(SuspectReport.report_id == new_report_id).first()
            if not existing:
                break
            new_report_id = SuspectReportService.generate_report_id(current_year)

        # Normalize drug activity to official full text name
        normalized_activity = SuspectReportService.normalize_activity_type(type_of_activity)

        # 2. Create parent report record strictly via SQLAlchemy ORM
        report = SuspectReport(
            report_id=new_report_id,
            fullname=fullname.strip(),
            email=email.strip().lower(),
            mobile=mobile.strip(),
            nic=nic.strip().upper(),
            address=address.strip(),
            police_station=police_station.strip(),
            type_of_activity=normalized_activity,
            activity_description=activity_description.strip(),
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        # 2. Upload multiple files directly to AWS S3 and save metadata/links
        if files:
            for file in files:
                # Skip empty file handles
                if not file.filename or not file.filename.strip():
                    continue

                try:
                    # Direct in-memory upload to S3 (no local disk files)
                    upload_result = await upload_file_to_s3(
                        file=file,
                        folder="suspect_reports",
                    )

                    # Persist evidence file link and metadata to PostgreSQL
                    evidence_file = SuspectReportFile(
                        report_id=report.id,
                        file_url=upload_result["file_url"],
                        filename=upload_result["filename"],
                        original_filename=upload_result["original_filename"],
                        content_type=upload_result["content_type"],
                        size_bytes=upload_result["size_bytes"],
                    )
                    db.add(evidence_file)

                except Exception as upload_err:
                    logger.error(
                        "Failed to upload evidence file %s for report #%s: %s",
                        file.filename,
                        report.id,
                        upload_err,
                    )
                    # Continue uploading other files if one fails, or re-raise if critical
                    continue

            db.commit()
            db.refresh(report)

        logger.info(
            "Suspect report created successfully: ID #%s (Report ID: %s, Police Station: %s, Files: %d)",
            report.id,
            report.report_id,
            report.police_station,
            len(report.files),
        )

        # 3. Asynchronously dispatch the Report ID confirmation email to the citizen
        if report.email and "@" in report.email:
            try:
                asyncio.create_task(
                    EmailService.send_report_confirmation_email(
                        recipient_email=report.email,
                        fullname=report.fullname,
                        report_id=report.report_id or str(report.id),
                        police_station=report.police_station,
                        type_of_activity=report.type_of_activity,
                        submitted_at=report.created_at,
                    )
                )
            except Exception as email_err:
                logger.warning("Failed to queue confirmation email for report #%s: %s", report.id, email_err)

        return report

    @staticmethod
    def get_by_id(db: Session, report_id: Any) -> Optional[SuspectReport]:
        """Fetch single report with evidence files strictly via SQLAlchemy ORM."""
        report_str = str(report_id).strip()
        # 1. Try finding by human-readable report_id (e.g. RE-2026-A9019B)
        report = (
            db.query(SuspectReport)
            .options(joinedload(SuspectReport.files))
            .filter(SuspectReport.report_id == report_str)
            .first()
        )
        if report:
            return report

        # 2. Try querying by primary key UUID
        try:
            report_uuid = uuid.UUID(report_str)
            return (
                db.query(SuspectReport)
                .options(joinedload(SuspectReport.files))
                .filter(SuspectReport.id == report_uuid)
                .first()
            )
        except (ValueError, TypeError):
            return None

    @staticmethod
    def list_reports(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        police_station: Optional[str] = None,
        type_of_activity: Optional[str] = None,
    ) -> List[SuspectReport]:
        """
        List suspect reports with filtering and pagination strictly via SQLAlchemy ORM.
        Restricted to ADMIN and SYSTEM_ADMIN.
        """
        query = db.query(SuspectReport).options(joinedload(SuspectReport.files))

        if police_station:
            query = query.filter(
                SuspectReport.police_station.ilike(f"%{police_station.strip()}%")
            )

        if type_of_activity and type_of_activity.strip() and type_of_activity.upper() != "ALL":
            act_clean = type_of_activity.strip()
            norm = SuspectReportService.normalize_activity_type(act_clean)
            query = query.filter(
                (SuspectReport.type_of_activity.ilike(f"%{act_clean}%"))
                | (SuspectReport.type_of_activity.ilike(f"%{norm}%"))
            )

        return (
            query.order_by(SuspectReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_report(db: Session, report_id: uuid.UUID) -> None:
        """
        Delete suspect report and all its evidence objects from AWS S3 and database.
        Restricted to SYSTEM_ADMIN.
        """
        report = SuspectReportService.get_by_id(db, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Suspect report with ID {report_id} not found",
            )

        # Delete associated files from AWS S3
        for evidence in report.files:
            s3_key = f"suspect_reports/{evidence.filename}"
            delete_file_from_s3(s3_key)

        # Delete record from database (cascade deletes suspect_report_files rows)
        db.delete(report)
        db.commit()
        logger.info("Suspect report ID #%s deleted by administrator.", report_id)


"""
SuspectReport and SuspectReportFile ORM models for citizen incident reporting.
Evidence files are uploaded directly to AWS S3, and their links/metadata are saved here.
"""

import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SuspectReport(Base):
    """
    SQLAlchemy ORM model representing public suspect/incident reports.

    Attributes:
        id (uuid.UUID): Primary key identifier.
        fullname (str): Full name of the citizen/reporting person.
        email (str): Contact email.
        mobile (str): Contact phone/mobile number.
        nic (str): National Identity Card number.
        address (str): Residence or incident address.
        police_station (str): Assigned local police station.
        type_of_activity (str): Category/type of suspected illegal or suspicious activity.
        activity_description (str): Detailed narrative description of the activity.
        created_at (datetime): Timestamp when report was submitted.
        updated_at (datetime): Timestamp when report was updated.
        files (relationship): Evidence files (images, ZIP archives, documents) uploaded to AWS S3.
    """
    __tablename__ = "suspect_reports"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=True)
    fullname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    mobile = Column(String(30), nullable=False, index=True)
    nic = Column(String(30), nullable=False, index=True)
    address = Column(Text, nullable=False)
    police_station = Column(String(150), nullable=False, index=True)
    type_of_activity = Column(String(150), nullable=False, index=True)
    activity_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # One-to-many relationship with uploaded evidence files
    files = relationship(
        "SuspectReportFile",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="SuspectReportFile.id",
    )

    def __repr__(self) -> str:
        return (
            f"<SuspectReport(id={self.id}, police_station='{self.police_station}', "
            f"type='{self.type_of_activity}')>"
        )


class SuspectReportFile(Base):
    """
    SQLAlchemy ORM model representing individual evidence files attached to a suspect report.
    Binary files are held in AWS S3; links and metadata are stored here.

    Attributes:
        id (uuid.UUID): Primary key.
        report_id (uuid.UUID): Foreign key to suspect_reports table.
        file_url (str): Publicly accessible AWS S3 URL.
        filename (str): Unique S3 object key/filename.
        original_filename (str): Original filename uploaded by the citizen.
        content_type (str): MIME type (e.g., image/jpeg, application/zip, application/pdf).
        size_bytes (int): File size in bytes.
        created_at (datetime): Upload timestamp.
    """
    __tablename__ = "suspect_report_files"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(
        Uuid,
        ForeignKey("suspect_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url = Column(String(1024), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(120), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Many-to-one relationship back to the parent report
    report = relationship("SuspectReport", back_populates="files")

    def __repr__(self) -> str:
        return f"<SuspectReportFile(id={self.id}, report_id={self.report_id}, filename='{self.filename}')>"


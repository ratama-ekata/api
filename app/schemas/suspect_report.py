"""
Pydantic schemas for suspect report creation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SuspectReportFileResponse(BaseModel):
    """Schema for individual evidence file attached to a suspect report."""
    id: uuid.UUID
    file_url: str = Field(..., description="Public AWS S3 link for the evidence file")
    filename: str = Field(..., description="Unique S3 object key")
    original_filename: str = Field(..., description="Original uploaded filename")
    content_type: str = Field(..., description="MIME content type")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SuspectReportResponse(BaseModel):
    """Schema for suspect report details returned to authorized administrators."""
    id: uuid.UUID
    fullname: str = Field(..., description="Citizen full name")
    email: str = Field(..., description="Contact email")
    mobile: str = Field(..., description="Contact phone/mobile number")
    nic: str = Field(..., description="National Identity Card number")
    address: str = Field(..., description="Address details")
    police_station: str = Field(..., description="Designated police station")
    type_of_activity: str = Field(..., description="Nature/category of suspicious activity")
    activity_description: str = Field(..., description="Detailed description of the incident")
    created_at: Optional[datetime] = None
    files: List[SuspectReportFileResponse] = Field(
        default_factory=list,
        description="Evidence files (images, zip files, documents) uploaded to AWS S3",
    )
    report_id: Optional[str] = None
    referenceNumber: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SuspectReportCreate(BaseModel):
    """Schema for direct JSON-based suspect report submission."""
    fullname: Optional[str] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None
    nic: Optional[str] = None
    address: Optional[str] = None
    police_station: Optional[str] = None
    policeStation: Optional[str] = None
    type_of_activity: Optional[str] = None
    activityType: Optional[str] = None
    activity_description: Optional[str] = None
    description: Optional[str] = None

    def get_fullname(self) -> str:
        return (self.fullname or self.fullName or "").strip()

    def get_email(self) -> str:
        return (self.email or "not_provided@ratamaekata.gov.lk").strip()

    def get_mobile(self) -> str:
        return (self.mobile or self.phone or "").strip()

    def get_nic(self) -> str:
        return (self.nic or "NOT_PROVIDED").strip()

    def get_address(self) -> str:
        return (self.address or "Not provided").strip()

    def get_police_station(self) -> str:
        return (self.police_station or self.policeStation or "").strip()

    def get_type_of_activity(self) -> str:
        return (self.type_of_activity or self.activityType or "other").strip()

    def get_activity_description(self) -> str:
        return (self.activity_description or self.description or "").strip()


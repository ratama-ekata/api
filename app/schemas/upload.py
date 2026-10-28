"""
Pydantic schemas for file upload responses and metadata serialization.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FileUploadResponse(BaseModel):
    """Schema for file upload response saved in PostgreSQL database with S3 public link."""
    id: uuid.UUID = Field(..., description="Database record UUID")
    filename: str = Field(..., description="Unique S3 filename/key")
    original_filename: str = Field(..., description="Original name of the uploaded file")
    file_url: str = Field(..., description="Public AWS S3 URL saved in the database")
    content_type: str = Field(..., description="MIME content type")
    size_bytes: int = Field(..., description="File size in bytes")
    user_id: uuid.UUID = Field(..., description="UUID of the user who uploaded the file")
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


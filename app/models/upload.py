"""
UploadedFile ORM model representing metadata and S3 URLs for uploaded files.
Files are held in AWS S3, and their remote links/metadata are saved in this table.
"""

import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UploadedFile(Base):
    """
    SQLAlchemy ORM model representing user-uploaded media stored in AWS S3.

    Attributes:
        id (uuid.UUID): Primary key identifier.
        filename (str): Unique UUID-based S3 filename.
        original_filename (str): Original uploaded filename.
        file_url (str): Publicly accessible AWS S3 URL.
        content_type (str): MIME type of the file.
        size_bytes (int): File size in bytes.
        user_id (uuid.UUID): Foreign key referencing the user who uploaded the file.
        created_at (datetime): Timestamp of upload.
        owner (relationship): Relationship back to the User model.
    """
    __tablename__ = "uploaded_files"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_url = Column(String(1024), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Many-to-one relationship back to the uploading user
    owner = relationship("User", back_populates="uploads")

    def __repr__(self) -> str:
        return f"<UploadedFile(id={self.id}, filename='{self.filename}', file_url='{self.file_url}')>"


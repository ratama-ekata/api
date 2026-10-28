"""
File upload controller: handles protected image uploads to AWS S3
and saves metadata & S3 links into PostgreSQL via SQLAlchemy ORM.
"""

import uuid
from typing import List, Set
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.upload import UploadedFile
from app.schemas.upload import FileUploadResponse
from app.services.s3_service import upload_file_to_s3, delete_file_from_s3
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/upload", tags=["File Uploads"])

ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
}


def validate_image_file(file: UploadFile) -> None:
    """Validate that the uploaded file is a supported image MIME type."""
    if not file.content_type or file.content_type.lower() not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
            ),
        )


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image directly to AWS S3 and save URL in database",
    description=(
        "Streams the image directly to AWS S3 without saving locally. "
        "The resulting public S3 URL and file metadata are saved in PostgreSQL. "
        "Requires Bearer JWT token."
    ),
)
@router.post("", include_in_schema=False, response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload directly to AWS S3"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Protected upload handler:
    1. Validates image MIME type.
    2. Streams file bytes in-memory to AWS S3 (no local disk files created).
    3. Persists S3 URL and metadata to PostgreSQL via SQLAlchemy ORM.
    4. Returns the created database record.
    """
    validate_image_file(file)

    # 1. Direct stream to AWS S3
    upload_result = await upload_file_to_s3(file, folder="images")

    # 2. Persist to PostgreSQL database strictly using SQLAlchemy ORM
    new_file_record = UploadedFile(
        filename=upload_result["filename"],
        original_filename=upload_result["original_filename"],
        file_url=upload_result["file_url"],
        content_type=upload_result["content_type"],
        size_bytes=upload_result["size_bytes"],
        user_id=current_user.id,
    )

    db.add(new_file_record)
    db.commit()
    db.refresh(new_file_record)

    return new_file_record


@router.get(
    "/my-files",
    response_model=List[FileUploadResponse],
    summary="List all uploaded files for the current user",
)
def get_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all file records and their saved S3 URLs for current user."""
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.user_id == current_user.id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return files


@router.get(
    "/{file_id}",
    response_model=FileUploadResponse,
    summary="Get single file record and S3 URL by ID",
)
def get_file_by_id(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve specific file metadata and S3 link from PostgreSQL."""
    file_record = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id,
        )
        .first()
    )
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File record not found or unauthorized",
        )
    return file_record


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file record from database and AWS S3",
)
def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a file from both PostgreSQL database and AWS S3 bucket."""
    file_record = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id,
        )
        .first()
    )
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File record not found or unauthorized",
        )

    # Delete from S3
    s3_key = f"images/{file_record.filename}"
    delete_file_from_s3(s3_key)

    # Delete record strictly using SQLAlchemy ORM
    db.delete(file_record)
    db.commit()

    return None


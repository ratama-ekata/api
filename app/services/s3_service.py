"""
AWS S3 service: handles direct in-memory file uploads, UUID filename generation,
and object deletions. No files are saved to local disk.
"""

import uuid
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_s3_client():
    """Initialize and return a boto3 S3 client instance."""
    client_kwargs: Dict[str, Any] = {
        "region_name": settings.AWS_REGION,
    }

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    if settings.AWS_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

    return boto3.client("s3", **client_kwargs)


def generate_unique_filename(original_filename: str) -> str:
    """Generate a collision-resistant unique filename using UUID4."""
    extension = ""
    if "." in original_filename:
        extension = f".{original_filename.rsplit('.', 1)[-1].lower()}"
    return f"{uuid.uuid4().hex}{extension}"


def build_s3_url(s3_key: str) -> str:
    """Build the public URL for an S3 object."""
    if settings.AWS_S3_CUSTOM_DOMAIN:
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"

    if settings.AWS_REGION == "us-east-1":
        return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


async def upload_file_to_s3(
    file: UploadFile,
    folder: str = "images",
) -> Dict[str, Any]:
    """
    Directly streams file bytes from memory to AWS S3 without saving to local disk.

    Args:
        file (UploadFile): Uploaded file from the request.
        folder (str): S3 bucket directory prefix.

    Returns:
        Dict[str, Any]: Upload metadata including public S3 URL.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename",
        )

    unique_filename = generate_unique_filename(file.filename)
    s3_key = f"{folder}/{unique_filename}" if folder else unique_filename
    content_type = file.content_type or "application/octet-stream"

    try:
        s3_client = get_s3_client()

        # Read bytes in memory directly (no local disk file created)
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)",
            )

        # Upload in-memory bytes to AWS S3
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )

        public_url = build_s3_url(s3_key)
        logger.info("Successfully uploaded %s to S3 bucket %s as %s", file.filename, settings.AWS_S3_BUCKET_NAME, s3_key)

        return {
            "filename": unique_filename,
            "s3_key": s3_key,
            "original_filename": file.filename,
            "file_url": public_url,
            "content_type": content_type,
            "size_bytes": file_size,
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error("AWS S3 ClientError [%s]: %s", error_code, error_msg)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AWS S3 Error ({error_code}): {error_msg}",
        )
    except BotoCoreError as e:
        logger.error("AWS BotoCore connection error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AWS S3 connection failure: {str(e)}",
        )
    finally:
        await file.seek(0)


def delete_file_from_s3(s3_key: str) -> bool:
    """Delete an object from AWS S3 bucket."""
    try:
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=s3_key)
        logger.info("Deleted %s from S3 bucket %s", s3_key, settings.AWS_S3_BUCKET_NAME)
        return True
    except Exception as e:
        logger.warning("Failed to delete %s from S3: %s", s3_key, str(e))
        return False


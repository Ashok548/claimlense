"""
Cloudflare R2 service using boto3 (S3-compatible API).
Used by FastAPI to download uploaded bills from R2 for OCR processing.
"""

import io
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

from app.config import settings

_r2_client = None


def get_r2_client():
    global _r2_client
    if _r2_client is None:
        _r2_client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _r2_client


def download_file(s3_key: str) -> bytes:
    """Download a file from R2 and return its raw bytes."""
    client = get_r2_client()
    response = client.get_object(Bucket=settings.r2_bucket_name, Key=s3_key)
    return response["Body"].read()


def upload_file(s3_key: str, data: bytes, content_type: str = "application/pdf") -> str:
    """Upload bytes to R2, return the object key."""
    client = get_r2_client()
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=s3_key,
        Body=data,
        ContentType=content_type,
    )
    return s3_key


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned download URL valid for `expires_in` seconds."""
    client = get_r2_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": s3_key},
        ExpiresIn=expires_in,
    )
    return url


def object_exists(s3_key: str) -> bool:
    """Return True if *s3_key* already exists in R2, False otherwise.

    Uses HeadObject which is cheap (no body transfer).  A missing object
    raises a ClientError with code '404' or 'NoSuchKey'; any other error
    is re-raised so callers can decide whether to fail or regenerate.
    """
    client = get_r2_client()
    try:
        client.head_object(Bucket=settings.r2_bucket_name, Key=s3_key)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            return False
        logger.warning("s3_service.object_exists: unexpected error for key %r: %s", s3_key, exc)
        raise

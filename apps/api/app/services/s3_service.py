"""
Cloudflare R2 service using boto3 (S3-compatible API).
Used by FastAPI to download uploaded bills from R2 for OCR processing.
"""

import io

import boto3
from botocore.config import Config

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

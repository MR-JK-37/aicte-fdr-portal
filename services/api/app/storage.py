"""Thin S3-compatible client for Garage (see docs/plan.md / progress.md for
why Garage rather than MinIO). Garage speaks the S3 API, so boto3 works
unmodified with path-style addressing and a dummy AWS region.
"""

import boto3

from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.garage_endpoint,
        aws_access_key_id=settings.garage_access_key,
        aws_secret_access_key=settings.garage_secret_key,
        region_name="garage",
    )


def put_object(
    key: str, data: bytes, content_type: str = "application/octet-stream"
) -> None:
    client = get_s3_client()
    client.put_object(
        Bucket=settings.garage_bucket, Key=key, Body=data, ContentType=content_type
    )


def get_object(key: str) -> bytes:
    client = get_s3_client()
    resp = client.get_object(Bucket=settings.garage_bucket, Key=key)
    return resp["Body"].read()


def presigned_put_url(key: str, expires_in: int = 900) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.garage_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def presigned_get_url(key: str, expires_in: int = 900) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.garage_bucket, "Key": key},
        ExpiresIn=expires_in,
    )

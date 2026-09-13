"""S3 presigned URL generation — root CLAUDE.md media pattern (S3 +
CloudFront, presigned URLs for upload, never through Lambda) and
backend/CLAUDE.md "S3 presigned URL generation" pattern, implemented
verbatim. Every presigned URL is scoped to exactly one object key (never
a bucket-wide grant) — root CLAUDE.md "AWS Best Practices" least-privilege
guardrail, applied at the call-site level; the IAM policy backing this
Lambda's execution role is Infra's to scope, not this module's.

`MEDIA_CDN_DOMAIN` (CloudFront distribution domain) is a new env var, not
yet listed in backend/CLAUDE.md's table — added here because photo/claim
responses need to resolve a stored `s3_key` to a servable URL. Flagged for
review; ask Infra to confirm the real CloudFront domain name once
provisioned.
"""
from __future__ import annotations

import os
import uuid

import boto3
from botocore.config import Config

from app.core.errors import AppError

_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}

_UPLOAD_EXPIRES_IN = 600  # 10 minutes — backend/CLAUDE.md pattern.

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", config=Config(signature_version="s3v4"))
    return _s3_client


def _get_bucket() -> str:
    bucket = os.environ.get("S3_MEDIA_BUCKET")
    if not bucket:
        raise RuntimeError("S3_MEDIA_BUCKET is not set — see root CLAUDE.md 'Environment Variables'.")
    return bucket


def _extension_for(content_type: str) -> str:
    return _CONTENT_TYPE_EXTENSIONS.get(content_type.lower(), "")


def generate_upload_url(key: str, content_type: str) -> tuple[str, int]:
    url = _get_s3_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": _get_bucket(), "Key": key, "ContentType": content_type},
        ExpiresIn=_UPLOAD_EXPIRES_IN,
    )
    return url, _UPLOAD_EXPIRES_IN


def generate_location_photo_upload_url(location_id: int, content_type: str) -> tuple[str, str, int]:
    """POST /locations/{id}/photos/upload-url."""
    if content_type.lower() not in _CONTENT_TYPE_EXTENSIONS:
        raise AppError(400, "Unsupported content_type for a photo upload", "unsupported_content_type")
    key = f"locations/{location_id}/photos/{uuid.uuid4().hex}{_extension_for(content_type)}"
    url, expires_in = generate_upload_url(key, content_type)
    return url, key, expires_in


def generate_claim_document_upload_url(claimant_user_id: str, content_type: str) -> tuple[str, str, int]:
    """Supporting-document upload for the `document_upload` claim proof
    path (docs/API_CONTRACTS.md "Claim flow"). Not itself a documented
    Phase 1 endpoint (the contract expects the client to already hold an
    `s3_key`) — kept here so the presign logic has one home if/when a
    dedicated upload-url route is added; unused by any router today.
    """
    ext = _extension_for(content_type) or ".pdf"
    key = f"claims/{claimant_user_id}/documents/{uuid.uuid4().hex}{ext}"
    url, expires_in = generate_upload_url(key, content_type)
    return url, key, expires_in


def resolve_media_url(s3_key: str) -> str:
    """Resolve a stored S3 object key to a CloudFront-served URL. Never a
    stored full URL (docs/API_CONTRACTS.md note at the top of the Photos
    section) — resolved at read time so a CDN domain change never touches
    stored data.
    """
    domain = os.environ.get("MEDIA_CDN_DOMAIN")
    if not domain:
        # Local/dev fallback so responses are still usable before a
        # CloudFront distribution exists — never used once MEDIA_CDN_DOMAIN
        # is set in a real environment.
        domain = f"{_get_bucket()}.s3.amazonaws.com"
    return f"https://{domain}/{s3_key}"

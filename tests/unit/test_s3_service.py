"""Unit test: S3 presigned URL generation — mocked boto3 client (tests/CLAUDE.md
"ALWAYS mock AWS calls ... instead of hitting real S3" / root CLAUDE.md AWS
Best Practices). No real `boto3.client("s3", ...)` call is ever made here —
`app.services.s3_service._get_s3_client` is monkeypatched to return a stub
object, so there is no network call to mock at the HTTP layer at all.
"""
from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.services import s3_service


class _FakeS3Client:
    """Stub replacing the real boto3 S3 client. Records what it was asked
    to sign and returns a deterministic fake URL — never talks to AWS.
    """

    def __init__(self):
        self.calls: list[dict] = []

    def generate_presigned_url(self, operation, Params, ExpiresIn):
        self.calls.append({"operation": operation, "params": Params, "expires_in": ExpiresIn})
        return f"https://fake-s3.example.com/{Params['Bucket']}/{Params['Key']}?signed=1"


@pytest.fixture
def fake_s3(monkeypatch: pytest.MonkeyPatch) -> _FakeS3Client:
    client = _FakeS3Client()
    monkeypatch.setattr(s3_service, "_get_s3_client", lambda: client)
    return client


def test_generate_location_photo_upload_url_returns_scoped_key(fake_s3: _FakeS3Client):
    url, key, expires_in = s3_service.generate_location_photo_upload_url(456, "image/jpeg")

    assert key.startswith("locations/456/photos/")
    assert key.endswith(".jpg")
    assert expires_in == 600
    assert url.endswith(f"/{key}?signed=1")
    # Exactly one object key was presigned — never a bucket-wide grant
    # (root CLAUDE.md AWS Best Practices, least privilege).
    assert len(fake_s3.calls) == 1
    assert fake_s3.calls[0]["params"]["Key"] == key
    assert fake_s3.calls[0]["operation"] == "put_object"


def test_generate_location_photo_upload_url_rejects_unsupported_content_type(fake_s3: _FakeS3Client):
    with pytest.raises(AppError) as exc_info:
        s3_service.generate_location_photo_upload_url(456, "application/zip")
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "unsupported_content_type"
    assert fake_s3.calls == []  # never even attempted to presign


def test_generate_claim_document_upload_url_scopes_key_to_claimant(fake_s3: _FakeS3Client):
    url, key, expires_in = s3_service.generate_claim_document_upload_url(
        "claimant-sub-123", "application/pdf"
    )
    assert key.startswith("claims/claimant-sub-123/documents/")
    assert key.endswith(".pdf")


def test_resolve_media_url_uses_cdn_domain_when_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEDIA_CDN_DOMAIN", "cdn.example.com")
    url = s3_service.resolve_media_url("locations/1/photos/abc.jpg")
    assert url == "https://cdn.example.com/locations/1/photos/abc.jpg"


def test_resolve_media_url_falls_back_to_bucket_when_cdn_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MEDIA_CDN_DOMAIN", raising=False)
    monkeypatch.setenv("S3_MEDIA_BUCKET", "my-test-bucket")
    url = s3_service.resolve_media_url("locations/1/photos/abc.jpg")
    assert url == "https://my-test-bucket.s3.amazonaws.com/locations/1/photos/abc.jpg"

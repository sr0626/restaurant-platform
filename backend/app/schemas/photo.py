"""Photo sub-resource of /locations — see docs/API_CONTRACTS.md "Photos
(restaurant_photo, sub-resource of /locations/{id})".
"""
from __future__ import annotations

from pydantic import BaseModel


class UploadUrlRequest(BaseModel):
    content_type: str


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int


class PhotoCreate(BaseModel):
    s3_key: str
    is_cover: bool = False


class PhotoUpdate(BaseModel):
    display_order: int | None = None
    is_cover: bool | None = None


class PhotoOut(BaseModel):
    id: int
    location_id: int
    url: str
    is_cover: bool
    display_order: int

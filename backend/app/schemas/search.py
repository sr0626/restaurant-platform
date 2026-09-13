"""Response shapes for GET /search — see docs/API_CONTRACTS.md."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.cuisine import CuisineTagOut


class NearestLocationOut(BaseModel):
    location_id: int
    distance_mi: float
    city: str
    state: str
    is_verified: bool
    is_paid: bool
    is_open_now: bool | None


class SearchResultOut(BaseModel):
    brand_id: int
    name: str
    slug: str
    is_claimed: bool
    cuisine_tags: list[CuisineTagOut]
    nearest_location: NearestLocationOut
    location_count_nearby: int
    cover_photo_url: str | None


class SearchResponse(BaseModel):
    results: list[SearchResultOut]
    page: int
    page_size: int
    total: int

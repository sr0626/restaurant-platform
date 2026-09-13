"""Unit test: photo gallery cap logic (2 free / 10 paid) — DECISIONS.md
"Photo gallery: 2 photos free, 10 photos paid per location" and
`app/services/photo_service.py`.

Uses a fake AsyncSession (add/flush/commit/refresh/delete no-ops) and
monkeypatches the count/lookup helpers so the cap-enforcement branch in
`create_photo` is exercised without a real DB.
"""
from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.models.restaurant_location import RestaurantLocation
from app.models.restaurant_photo import RestaurantPhoto
from app.schemas.photo import PhotoCreate
from app.services import photo_service


class _FakeSession:
    def __init__(self):
        self.added = []
        self.deleted = []

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


def _location(*, is_paid: bool, location_id: int = 1) -> RestaurantLocation:
    return RestaurantLocation(
        id=location_id,
        brand_id=1,
        address_line1="1 Main St",
        city="Plano",
        state="TX",
        postal_code="75024",
        is_paid=is_paid,
    )


def test_gallery_limit_for_free_tier_is_two():
    assert photo_service.gallery_limit_for(False) == 2


def test_gallery_limit_for_paid_tier_is_ten():
    assert photo_service.gallery_limit_for(True) == 10


@pytest.mark.asyncio
async def test_create_photo_rejects_beyond_free_cap(monkeypatch: pytest.MonkeyPatch):
    async def _fake_count(db, location_id):
        return 2  # already at the free-tier limit

    monkeypatch.setattr(photo_service, "count_gallery_photos", _fake_count)

    db = _FakeSession()
    location = _location(is_paid=False)
    body = PhotoCreate(s3_key="locations/1/photos/x.jpg", is_cover=False)

    with pytest.raises(AppError) as exc_info:
        await photo_service.create_photo(db, location, body, uploaded_by="owner-sub")
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "gallery_limit_reached"
    assert db.added == []  # nothing was persisted


@pytest.mark.asyncio
async def test_create_photo_allows_under_free_cap(monkeypatch: pytest.MonkeyPatch):
    async def _fake_count(db, location_id):
        return 1  # one below the free-tier limit of 2

    monkeypatch.setattr(photo_service, "count_gallery_photos", _fake_count)

    db = _FakeSession()
    location = _location(is_paid=False)
    body = PhotoCreate(s3_key="locations/1/photos/x.jpg", is_cover=False)

    photo = await photo_service.create_photo(db, location, body, uploaded_by="owner-sub")
    assert photo.is_cover is False
    assert photo.display_order == 1
    assert db.added == [photo]


@pytest.mark.asyncio
async def test_create_photo_rejects_beyond_paid_cap(monkeypatch: pytest.MonkeyPatch):
    async def _fake_count(db, location_id):
        return 10  # already at the paid-tier limit

    monkeypatch.setattr(photo_service, "count_gallery_photos", _fake_count)

    db = _FakeSession()
    location = _location(is_paid=True)
    body = PhotoCreate(s3_key="locations/1/photos/x.jpg", is_cover=False)

    with pytest.raises(AppError) as exc_info:
        await photo_service.create_photo(db, location, body, uploaded_by="owner-sub")
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_photo_cover_replaces_not_stacks(monkeypatch: pytest.MonkeyPatch):
    existing_cover = RestaurantPhoto(id=5, location_id=1, s3_key="old.jpg", is_cover=True)

    async def _fake_get_cover(db, location_id):
        return existing_cover

    monkeypatch.setattr(photo_service, "get_cover_photo", _fake_get_cover)

    db = _FakeSession()
    location = _location(is_paid=False)
    body = PhotoCreate(s3_key="locations/1/photos/new-cover.jpg", is_cover=True)

    new_photo = await photo_service.create_photo(db, location, body, uploaded_by="owner-sub")
    assert new_photo.is_cover is True
    assert existing_cover in db.deleted  # old cover removed, not stacked

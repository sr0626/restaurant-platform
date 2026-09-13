"""BUG REPORT (proven, not fixed — tests/CLAUDE.md "NEVER modify application
code to make a test pass ... report the bug instead"):

`app/services/photo_service.py::get_gallery_photos` returns EVERY
`is_cover=False` row for a location, with no tier-based limit applied at
READ time:

    async def get_gallery_photos(db, location_id):
        result = await db.execute(
            select(RestaurantPhoto)
            .where(RestaurantPhoto.location_id == location_id, RestaurantPhoto.is_cover == False)
            .order_by(RestaurantPhoto.display_order)
        )
        return list(result.scalars().all())

The 2-free/10-paid gallery cap (DECISIONS.md "Photo gallery: 2 photos free,
10 photos paid per location") is enforced ONLY on write, in
`photo_service.create_photo` / `update_photo` (count-check against
`gallery_limit_for(location.is_paid)` before inserting). Nothing re-checks
the tier at read time, and `get_gallery_photos` isn't even given the
location's `is_paid` flag to do so.

Concrete failure scenario this creates: a location is paid (limit 10),
owner uploads 6 gallery photos (all allowed, under the paid cap). The
location's Stripe subscription then lapses (payment failure — DECISIONS.md
"Payment failure = immediate free tier, no grace period" — is_paid flips to
False immediately, no photos are deleted, per root CLAUDE.md "Paid content
behaviour: Downgrade ... content hides immediately (is_paid=false), NOT
deleted"). `GET /locations/{id}` (via `location_service._location_to_out`,
which calls `photo_service.get_gallery_photos` directly) still returns all
6 gallery photos to the public, even though the location is now free tier
and root CLAUDE.md is explicit: "is_paid=false locations: dish photos
beyond the free gallery limit ... are NOT returned by API." This is a real
data-exposure/contract violation, not merely a cosmetic one — paid-tier
content (extra gallery photos) is served to the public after downgrade.

This test proves the bug rather than fixing `photo_service.py` (out of
scope for QA — tests/CLAUDE.md "You do NOT write application code"). It is
expected to FAIL against the current implementation (`xfail(strict=True)`
below) and should start reliably passing — at which point this xfail
marker should be removed — once Backend Dev adds a tier-aware slice, e.g.
`get_gallery_photos(db, location_id, limit=gallery_limit_for(location.is_paid))`.
"""
from __future__ import annotations

import pytest

from app.models.restaurant_photo import RestaurantPhoto
from app.services import photo_service


class _FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class _FakeSession:
    def __init__(self, photos: list[RestaurantPhoto]):
        self._photos = photos

    async def execute(self, _stmt):
        return _FakeResult(self._photos)


def _photos(count: int, location_id: int = 1) -> list[RestaurantPhoto]:
    return [
        RestaurantPhoto(id=i, location_id=location_id, s3_key=f"p{i}.jpg", is_cover=False, display_order=i)
        for i in range(count)
    ]


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "BUG: photo_service.get_gallery_photos does not cap results to the "
        "location's current tier limit at read time (only enforced on "
        "write) — see this file's module docstring for the full report."
    ),
)
async def test_get_gallery_photos_caps_to_free_tier_limit_after_downgrade():
    # Location previously paid, uploaded 6 gallery photos (valid under the
    # paid cap of 10 at the time), then downgraded to free tier (cap 2).
    db = _FakeSession(_photos(6))

    photos = await photo_service.get_gallery_photos(db, location_id=1)

    # Root CLAUDE.md: "is_paid=false locations: dish photos beyond the free
    # gallery limit ... are NOT returned by API."
    assert len(photos) <= photo_service.FREE_GALLERY_LIMIT

"""Regression test for a real bug QA found and Backend Dev fixed on
`fix/photo-gallery-read-cap` (commit d4a37f8): `photo_service.get_gallery_photos`
returned every gallery photo with no tier-based limit applied at READ time —
only `create_photo`/`update_photo` enforced the 2-free/10-paid cap on write.

Moved here (from a `tests/unit/` version with a hand-rolled fake session) once
it became clear the fake session's `execute()` ignored the real SQL `.limit()`
clause entirely and always returned every photo regardless of the query —
so it could never actually prove the fix works, only that the call didn't
raise. This version exercises the real `.limit()` against a real (in-memory
SQLite) database, which is what the bug was actually about.

Concrete scenario (root CLAUDE.md "Paid content behaviour": downgrade hides
paid content immediately, is_paid=false, NOT deleted; DECISIONS.md "Payment
failure = immediate free tier, no grace period"): a location is paid (limit
10), uploads 6 gallery photos (valid under the paid cap), then its
subscription lapses — is_paid flips to False immediately, no photos are
deleted. `GET /locations/{id}` must stop returning photos beyond the free
limit (2) immediately.
"""
from __future__ import annotations

import pytest

from app.services import photo_service
from factories import create_brand, create_location, create_owner, create_photo


@pytest.mark.asyncio
async def test_get_gallery_photos_caps_to_free_tier_limit_after_downgrade(db_session):
    owner = await create_owner(db_session)
    brand = await create_brand(db_session, owner_id=owner.id, is_claimed=True)
    # Currently free tier (is_paid=False) — mirrors the location's state
    # *now*, i.e. after the downgrade already happened. The 6 photos below
    # simulate rows that were legitimately created earlier while the
    # location was still paid; nothing here re-runs that write-time history,
    # since only the read-time behavior is under test.
    location = await create_location(db_session, brand_id=brand.id, is_paid=False)
    for i in range(6):
        await create_photo(db_session, location_id=location.id, display_order=i)
    await db_session.commit()

    photos = await photo_service.get_gallery_photos(db_session, location_id=location.id, is_paid=location.is_paid)

    # Root CLAUDE.md: "is_paid=false locations: dish photos beyond the free
    # gallery limit ... are NOT returned by API."
    assert len(photos) == photo_service.FREE_GALLERY_LIMIT == 2
    # The kept photos are the lowest display_order ones (first uploaded),
    # not an arbitrary subset — confirms the LIMIT applies on top of the
    # existing ORDER BY display_order, not instead of it.
    assert [p.display_order for p in photos] == [0, 1]


@pytest.mark.asyncio
async def test_get_gallery_photos_returns_up_to_paid_limit_while_still_paid(db_session):
    owner = await create_owner(db_session)
    brand = await create_brand(db_session, owner_id=owner.id, is_claimed=True)
    location = await create_location(db_session, brand_id=brand.id, is_paid=True)
    for i in range(6):
        await create_photo(db_session, location_id=location.id, display_order=i)
    await db_session.commit()

    photos = await photo_service.get_gallery_photos(db_session, location_id=location.id, is_paid=location.is_paid)

    # 6 uploaded, paid limit is 10 — all 6 come back, none dropped.
    assert len(photos) == 6

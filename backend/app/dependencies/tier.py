"""is_paid() check dependency — backend/CLAUDE.md "Key Patterns" pattern,
implemented verbatim (adapted to the async session).

Not currently wired into a Phase 1 router: every Phase 1 read/write
endpoint gates paid-only *content* by omission at the data layer instead
(e.g. the photo gallery cap in `app/services/photo_service.py`), and the
paid-only *endpoints* this dependency would guard (deals, analytics,
custom landing page) are Phase 2 (backend/CLAUDE.md "Do NOT Build Yet").
Kept here, matching the documented pattern exactly, for Phase 2 endpoints
to depend on directly.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.dependencies.db import get_db
from app.models.restaurant_location import RestaurantLocation
from fastapi import Depends


async def require_paid_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
) -> bool:
    result = await db.execute(
        select(RestaurantLocation.is_paid).where(RestaurantLocation.id == location_id)
    )
    is_paid = result.scalar_one_or_none()
    if not is_paid:
        raise AppError(403, "Paid tier required", "paid_tier_required")
    return True

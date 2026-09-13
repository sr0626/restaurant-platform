"""location_manager cap-check helper.

FLAGGED GAP (see final task report): `docs/API_CONTRACTS.md` does not
define a manager-assignment endpoint (no `/locations/{id}/managers`
family, and it isn't in backend/CLAUDE.md's Phase 1 endpoint list either —
only `/search`, `/restaurants`, `/locations`, `/claim`, `/auth`), even
though root/backend CLAUDE.md's guardrails explicitly require enforcing
"no more than 2 active location_manager assignments per location on paid
tier". Since API_CONTRACTS.md is Architect's contract surface and
Backend Dev must not invent undocumented endpoints (root CLAUDE.md "NEVER
build features outside current phase scope" / architect/CLAUDE.md owns
contract design), no router calls this today. This module exists so the
cap-check logic (DECISIONS.md "Assignable location managers capped at 2")
is ready and correct the moment Architect adds the missing contract —
nothing here is wired into a live endpoint yet.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.location_manager import LocationManager
from app.models.restaurant_location import RestaurantLocation

MAX_ACTIVE_MANAGERS_PER_LOCATION_PAID = 2


async def count_active_managers(db: AsyncSession, location_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(LocationManager)
        .where(LocationManager.location_id == location_id, LocationManager.is_active == True)  # noqa: E712
    )
    return result.scalar_one()


async def assert_can_add_active_manager(db: AsyncSession, location: RestaurantLocation) -> None:
    """Raise 409 if adding one more active manager would exceed the cap.

    Only enforced on the paid tier (DECISIONS.md "Assignable location
    managers capped at 2 per location on paid tier") — no cap on free tier.
    """
    if not location.is_paid:
        return
    current = await count_active_managers(db, location.id)
    if current >= MAX_ACTIVE_MANAGERS_PER_LOCATION_PAID:
        raise AppError(
            409,
            f"This location already has the maximum of {MAX_ACTIVE_MANAGERS_PER_LOCATION_PAID} active managers allowed on the paid tier",
            "manager_cap_reached",
        )

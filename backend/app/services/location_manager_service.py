"""location_manager business logic for `/locations/{id}/managers` — see
docs/API_CONTRACTS.md "Location Managers".

`assert_can_add_active_manager` (the paid-tier 2-active-manager cap check,
DECISIONS.md "Assignable location managers capped at 2") was written ahead
of the contract that wires it to a live endpoint; that contract now exists
and `assign_manager` below is the wiring.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.location_manager import LocationManager
from app.models.restaurant_location import RestaurantLocation
from app.services import audit_service, cognito_service

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


def _to_out(manager: LocationManager):
    # Sync, not async — same posture as `s3_service`'s boto3 calls, called
    # directly (no `await`) from async service code elsewhere in this app;
    # `cognito_service` wraps blocking boto3 the same way `s3_service`
    # does, so this mapper stays sync too rather than faking an `await`
    # that never actually yields.
    #
    # Local import avoids a hard import-time dependency from this service
    # module onto the schemas package for the (uncommon) case something
    # ever needs this service without the API layer.
    from app.schemas.location_manager import LocationManagerOut

    return LocationManagerOut(
        id=manager.id,
        location_id=manager.location_id,
        user_id=manager.user_id,
        email=cognito_service.find_email_by_sub(manager.user_id),
        is_active=manager.is_active,
        assigned_by_owner_id=manager.assigned_by_owner_id,
        assigned_at=manager.assigned_at,
        revoked_at=manager.revoked_at,
    )


async def assign_manager(
    db: AsyncSession, location: RestaurantLocation, current_user, manager_email: str
):
    """POST /locations/{id}/managers.

    Order matters: resolve the email to a `sub` first (a `404
    manager_not_found` should not be preceded by a wasted cap-check), then
    enforce the paid-tier cap, then attempt the insert — the partial
    unique index (`uq_location_manager_active_user`, docs/DATA_MODEL.md)
    is the last line of defense against a concurrent duplicate active
    assignment and is caught below rather than leaking a raw DB integrity
    error (same pattern as `restaurant_service.delete_restaurant`'s
    `ON DELETE RESTRICT` catch).
    """
    sub = cognito_service.find_sub_by_email(manager_email)
    if sub is None:
        raise AppError(
            404,
            "No registered user exists with this email",
            "manager_not_found",
        )

    await assert_can_add_active_manager(db, location)

    manager = LocationManager(
        location_id=location.id,
        user_id=sub,
        assigned_by_owner_id=current_user.owner_account_id,
        is_active=True,
    )
    db.add(manager)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            409,
            "This user already has an active manager assignment on this location",
            "already_active_manager",
        )

    await audit_service.log(
        db,
        table_name="location_manager",
        record_id=manager.id,
        action="create",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=None,
        new_val={
            "location_id": manager.location_id,
            "user_id": manager.user_id,
            "is_active": manager.is_active,
        },
    )
    await db.commit()
    return _to_out(manager)


async def list_managers(db: AsyncSession, location_id: int, active_only: bool):
    """GET /locations/{id}/managers."""
    stmt = select(LocationManager).where(LocationManager.location_id == location_id)
    if active_only:
        stmt = stmt.where(LocationManager.is_active == True)  # noqa: E712
    stmt = stmt.order_by(LocationManager.id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(row) for row in rows]


async def deactivate_manager(
    db: AsyncSession, location_id: int, manager_id: int, current_user
) -> None:
    """DELETE /locations/{id}/managers/{manager_id}.

    Soft-deactivate only — sets `is_active=false` + `revoked_at=now()`,
    never deletes the row (docs/API_CONTRACTS.md). Idempotent for an
    already-inactive row: returns with no error and no side effect (no
    audit row, no `revoked_at` overwrite) rather than 404/409 — plain
    REST-delete idempotency, per the contract. A `manager_id` that never
    existed for this location is a genuine 404, not a no-op.
    """
    manager = await db.get(LocationManager, manager_id)
    if manager is None or manager.location_id != location_id:
        raise AppError(404, "Manager assignment not found", "not_found")

    if not manager.is_active:
        return

    old_val = {"is_active": manager.is_active, "revoked_at": None}
    manager.is_active = False
    manager.revoked_at = datetime.now(timezone.utc)
    new_val = {"is_active": manager.is_active, "revoked_at": manager.revoked_at.isoformat()}

    await audit_service.log(
        db,
        table_name="location_manager",
        record_id=manager.id,
        action="update",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=old_val,
        new_val=new_val,
    )
    await db.commit()

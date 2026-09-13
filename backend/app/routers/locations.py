"""restaurant_location endpoints + hours/photos/managers sub-resources. See
docs/API_CONTRACTS.md "Locations (restaurant_location)" and "Location
Managers".

Public: GET /locations/{id} (backend/CLAUDE.md "Public Routes"). Every
other route requires auth, re-validated server-side on every write (never
the JWT claims alone) via the dependencies in `app/dependencies/auth.py`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    CurrentUser,
    require_location_owner_only,
    require_location_owner_or_admin,
    require_location_read_access,
    require_location_write_access,
    require_owner,
)
from app.dependencies.db import get_db
from app.schemas.hours import HoursReplaceRequest, HoursResponse
from app.schemas.location import LocationCreate, LocationOut, LocationUpdate
from app.schemas.location_manager import (
    AssignManagerRequest,
    LocationManagerListResponse,
    LocationManagerOut,
)
from app.schemas.photo import PhotoCreate, PhotoOut, PhotoUpdate, UploadUrlRequest, UploadUrlResponse
from app.services import location_manager_service, location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)) -> LocationOut:
    return await location_service.get_location(db, location_id)


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_owner),
) -> LocationOut:
    return await location_service.create_location(db, body, current_user)


@router.patch("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: int,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> LocationOut:
    return await location_service.update_location(db, location_id, body, current_user)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_owner_or_admin),
) -> None:
    await location_service.delete_location(db, location_id, current_user)


@router.put("/{location_id}/hours", response_model=HoursResponse)
async def replace_location_hours(
    location_id: int,
    body: HoursReplaceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> HoursResponse:
    return await location_service.replace_location_hours(db, location_id, body.hours, current_user)


@router.post("/{location_id}/photos/upload-url", response_model=UploadUrlResponse)
async def create_photo_upload_url(
    location_id: int,
    body: UploadUrlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> UploadUrlResponse:
    return await location_service.create_photo_upload_url(db, location_id, body.content_type)


@router.post(
    "/{location_id}/photos", response_model=PhotoOut, status_code=status.HTTP_201_CREATED
)
async def create_location_photo(
    location_id: int,
    body: PhotoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> PhotoOut:
    return await location_service.create_location_photo(db, location_id, body, current_user)


@router.patch("/{location_id}/photos/{photo_id}", response_model=PhotoOut)
async def update_location_photo(
    location_id: int,
    photo_id: int,
    body: PhotoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> PhotoOut:
    return await location_service.update_location_photo(db, location_id, photo_id, body)


@router.delete("/{location_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_photo(
    location_id: int,
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_write_access),
) -> None:
    await location_service.delete_location_photo(db, location_id, photo_id)


@router.post(
    "/{location_id}/managers",
    response_model=LocationManagerOut,
    status_code=status.HTTP_201_CREATED,
)
async def assign_location_manager(
    location_id: int,
    body: AssignManagerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_owner_only),
) -> LocationManagerOut:
    location = await location_service.get_location_or_404(db, location_id)
    return await location_manager_service.assign_manager(
        db, location, current_user, body.manager_email
    )


@router.get("/{location_id}/managers", response_model=LocationManagerListResponse)
async def list_location_managers(
    location_id: int,
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_read_access),
) -> LocationManagerListResponse:
    # Forced true for a manager caller (docs/API_CONTRACTS.md "GET
    # /locations/{id}/managers" — a manager sees who currently manages
    # this location, not the full removal history); owner/admin get the
    # `active_only` query param as given, default false (full history).
    effective_active_only = active_only or current_user.role == "manager"
    await location_service.get_location_or_404(db, location_id)
    results = await location_manager_service.list_managers(
        db, location_id, effective_active_only
    )
    return LocationManagerListResponse(results=results)


@router.delete(
    "/{location_id}/managers/{manager_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_location_manager(
    location_id: int,
    manager_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_location_owner_or_admin),
) -> None:
    await location_manager_service.deactivate_manager(
        db, location_id, manager_id, current_user
    )

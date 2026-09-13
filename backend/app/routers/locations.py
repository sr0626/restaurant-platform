"""restaurant_location endpoints + hours/photos sub-resources. See
docs/API_CONTRACTS.md "Locations (restaurant_location)".

Public: GET /locations/{id} (backend/CLAUDE.md "Public Routes"). Every
other route requires auth, re-validated server-side on every write (never
the JWT claims alone) via the dependencies in `app/dependencies/auth.py`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    CurrentUser,
    require_location_owner_or_admin,
    require_location_write_access,
    require_owner,
)
from app.dependencies.db import get_db
from app.schemas.hours import HoursReplaceRequest, HoursResponse
from app.schemas.location import LocationCreate, LocationOut, LocationUpdate
from app.schemas.photo import PhotoCreate, PhotoOut, PhotoUpdate, UploadUrlRequest, UploadUrlResponse
from app.services import location_service

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

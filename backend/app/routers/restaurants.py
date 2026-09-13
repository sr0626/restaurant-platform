"""restaurant_brand endpoints. See docs/API_CONTRACTS.md "Restaurants
(restaurant_brand)".

Public: GET /restaurants/{id}, GET /restaurants/{id}/locations
(backend/CLAUDE.md "Public Routes"). Everything else requires auth.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import CurrentUser, require_admin, require_brand_write_access, require_owner
from app.dependencies.db import get_db
from app.dependencies.pagination import Pagination, pagination_params
from app.schemas.restaurant import (
    LocationListResponse,
    RestaurantCreate,
    RestaurantOut,
    RestaurantUpdate,
)
from app.services import location_service, restaurant_service

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/{id_or_slug}", response_model=RestaurantOut)
async def get_restaurant(id_or_slug: str, db: AsyncSession = Depends(get_db)) -> RestaurantOut:
    """`id_or_slug` may be the numeric `restaurant_brand.id` or its `slug`
    (docs/API_CONTRACTS.md "GET /restaurants/{id}")."""
    return await restaurant_service.get_restaurant(db, id_or_slug)


@router.get("/{brand_id}/locations", response_model=LocationListResponse)
async def list_restaurant_locations(
    brand_id: int,
    pagination: Pagination = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> LocationListResponse:
    return await location_service.list_locations_for_brand(db, brand_id, pagination)


@router.post("", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    body: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_owner),
) -> RestaurantOut:
    return await restaurant_service.create_restaurant(db, body, current_user)


@router.patch("/{brand_id}", response_model=RestaurantOut)
async def update_restaurant(
    brand_id: int,
    body: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_brand_write_access),
) -> RestaurantOut:
    return await restaurant_service.update_restaurant(db, brand_id, body, current_user)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
) -> None:
    await restaurant_service.delete_restaurant(db, brand_id, current_user)

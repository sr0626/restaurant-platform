"""restaurant_brand CRUD — see docs/API_CONTRACTS.md "Restaurants
(restaurant_brand)".
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.restaurant_brand import RestaurantBrand
from app.models.restaurant_location import RestaurantLocation
from app.schemas.cuisine import CuisineTagOut
from app.schemas.restaurant import RestaurantCreate, RestaurantOut, RestaurantUpdate
from app.services import audit_service, auth_service, cuisine_service


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "restaurant"


async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    suffix = 2
    while True:
        result = await db.execute(select(RestaurantBrand.id).where(RestaurantBrand.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


async def _brand_to_out(db: AsyncSession, brand: RestaurantBrand) -> RestaurantOut:
    tags = await cuisine_service.get_brand_cuisine_tags(db, brand.id)
    count_result = await db.execute(
        select(func.count())
        .select_from(RestaurantLocation)
        .where(RestaurantLocation.brand_id == brand.id, RestaurantLocation.is_active == True)  # noqa: E712
    )
    location_count = count_result.scalar_one()
    return RestaurantOut(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        description=brand.description,
        is_claimed=brand.is_claimed,
        owner_id=brand.owner_id,
        cuisine_tags=[CuisineTagOut.model_validate(t) for t in tags],
        location_count=location_count,
    )


async def get_restaurant(db: AsyncSession, brand_id: int) -> RestaurantOut:
    brand = await db.get(RestaurantBrand, brand_id)
    if brand is None:
        raise AppError(404, "Restaurant not found", "not_found")
    return await _brand_to_out(db, brand)


async def get_brand_or_404(db: AsyncSession, brand_id: int) -> RestaurantBrand:
    brand = await db.get(RestaurantBrand, brand_id)
    if brand is None:
        raise AppError(404, "Restaurant not found", "not_found")
    return brand


async def create_restaurant(db: AsyncSession, body: RestaurantCreate, current_user) -> RestaurantOut:
    owner = await auth_service.get_or_create_owner_account(
        db, current_user.cognito_sub, current_user.email
    )
    base_slug = slugify(body.name)
    slug = await _unique_slug(db, base_slug)

    brand = RestaurantBrand(
        owner_id=owner.id,
        name=body.name,
        slug=slug,
        description=body.description,
        is_claimed=True,
        claimed_at=datetime.now(timezone.utc),
    )
    db.add(brand)
    await db.flush()

    if body.cuisine_tag_ids:
        await cuisine_service.set_brand_cuisine_tags(db, brand.id, body.cuisine_tag_ids)

    await audit_service.log(
        db,
        table_name="restaurant_brand",
        record_id=brand.id,
        action="create",
        actor_id=current_user.cognito_sub,
        actor_role="owner",
        old_val=None,
        new_val={"name": brand.name, "slug": brand.slug, "owner_id": brand.owner_id},
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(409, "A restaurant with a conflicting slug already exists", "slug_conflict")

    return await get_restaurant(db, brand.id)


async def update_restaurant(
    db: AsyncSession, brand_id: int, body: RestaurantUpdate, current_user
) -> RestaurantOut:
    brand = await get_brand_or_404(db, brand_id)

    old_val = {"name": brand.name, "description": brand.description}

    if body.name is not None:
        brand.name = body.name
    if body.description is not None:
        brand.description = body.description
    if body.cuisine_tag_ids is not None:
        await cuisine_service.set_brand_cuisine_tags(db, brand.id, body.cuisine_tag_ids)

    new_val = {"name": brand.name, "description": brand.description}

    await audit_service.log(
        db,
        table_name="restaurant_brand",
        record_id=brand.id,
        action="update",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=old_val,
        new_val=new_val,
    )
    await db.commit()
    return await get_restaurant(db, brand.id)


async def delete_restaurant(db: AsyncSession, brand_id: int, current_user) -> None:
    """restaurant_location.brand_id has ON DELETE RESTRICT — the DB refuses
    this delete while any location rows still reference the brand
    (docs/API_CONTRACTS.md "DELETE /restaurants/{id}"). Caught below and
    surfaced as a clean 409 rather than a leaked DB integrity error (root
    CLAUDE.md "NEVER expose internal stack details").
    """
    brand = await get_brand_or_404(db, brand_id)

    await audit_service.log(
        db,
        table_name="restaurant_brand",
        record_id=brand.id,
        action="delete",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val={"name": brand.name, "slug": brand.slug},
        new_val=None,
    )
    await db.delete(brand)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            409,
            "Cannot delete a restaurant that still has locations. Remove or reassign its locations first.",
            "brand_has_locations",
        )

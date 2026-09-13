"""cuisine_tag / restaurant_cuisine helpers.

Tags are joined at the brand level (docs/DATA_MODEL.md "restaurant_cuisine"
judgment call) — no location-level variant in Phase 1. No public write API
for `cuisine_tag` itself (admin-panel/seed only, per
`docs/DATA_MODEL.md`) — only the brand<->tag link is written here, via
`POST`/`PATCH /restaurants`.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cuisine_tag import CuisineTag
from app.models.restaurant_cuisine import RestaurantCuisine


async def get_brand_cuisine_tags(db: AsyncSession, brand_id: int) -> list[CuisineTag]:
    result = await db.execute(
        select(CuisineTag)
        .join(RestaurantCuisine, RestaurantCuisine.cuisine_tag_id == CuisineTag.id)
        .where(RestaurantCuisine.brand_id == brand_id)
        .order_by(CuisineTag.category, CuisineTag.display_name)
    )
    return list(result.scalars().all())


async def get_brand_cuisine_tags_bulk(
    db: AsyncSession, brand_ids: list[int]
) -> dict[int, list[CuisineTag]]:
    if not brand_ids:
        return {}
    result = await db.execute(
        select(RestaurantCuisine.brand_id, CuisineTag)
        .join(CuisineTag, RestaurantCuisine.cuisine_tag_id == CuisineTag.id)
        .where(RestaurantCuisine.brand_id.in_(brand_ids))
        .order_by(CuisineTag.category, CuisineTag.display_name)
    )
    by_brand: dict[int, list[CuisineTag]] = {bid: [] for bid in brand_ids}
    for brand_id, tag in result.all():
        by_brand.setdefault(brand_id, []).append(tag)
    return by_brand


async def set_brand_cuisine_tags(db: AsyncSession, brand_id: int, tag_ids: list[int]) -> None:
    """Full replace of a brand's cuisine tag links (used by
    POST/PATCH /restaurants' `cuisine_tag_ids`). Silently ignores ids that
    don't correspond to an active tag rather than erroring — a stale
    frontend-supplied id shouldn't fail the whole write.
    """
    await db.execute(delete(RestaurantCuisine).where(RestaurantCuisine.brand_id == brand_id))
    if not tag_ids:
        return
    result = await db.execute(
        select(CuisineTag.id).where(CuisineTag.id.in_(tag_ids), CuisineTag.is_active == True)  # noqa: E712
    )
    valid_ids = {row[0] for row in result.all()}
    for tag_id in tag_ids:
        if tag_id in valid_ids:
            db.add(RestaurantCuisine(brand_id=brand_id, cuisine_tag_id=tag_id))

"""restaurant_location CRUD, the /hours sub-resource, and the /photos
sub-resource orchestration — see docs/API_CONTRACTS.md "Locations
(restaurant_location)".
"""
from __future__ import annotations

from decimal import Decimal

from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.restaurant_brand import RestaurantBrand
from app.models.restaurant_location import RestaurantLocation
from app.schemas.hours import HourEntryIn, HoursResponse
from app.schemas.location import (
    GalleryPhotoOut,
    HoursOut,
    LocationCreate,
    LocationOut,
    LocationUpdate,
)
from app.schemas.photo import PhotoCreate, PhotoOut, PhotoUpdate, UploadUrlResponse
from app.schemas.restaurant import LocationListResponse, LocationSummaryOut
from app.services import audit_service, auth_service, hours_service, photo_service, s3_service


def _to_decimal(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


async def _sync_geom(db: AsyncSession, location_id: int, lat: float, lng: float) -> None:
    """Keep `geom` (the column `/search` actually queries) in sync with
    lat/lng on write — docs/DATA_MODEL.md judgment-call note: no DB
    trigger, so every writer path must remember to do this. `ST_MakePoint`
    takes (lng, lat) — PostGIS/GeoJSON x,y order, not (lat, lng).
    """
    await db.execute(
        update(RestaurantLocation)
        .where(RestaurantLocation.id == location_id)
        .values(geom=ST_SetSRID(ST_MakePoint(lng, lat), 4326))
    )


async def _location_to_out(db: AsyncSession, location: RestaurantLocation) -> LocationOut:
    hours_rows = await hours_service.get_hours_for_location(db, location.id)
    hours_by_day = {row.day_of_week: row for row in hours_rows}
    today = hours_service.today_weekday(location.timezone)
    is_open_now = hours_service.compute_is_open_now(hours_by_day.get(today), location.timezone)

    cover = await photo_service.get_cover_photo(db, location.id)
    gallery = await photo_service.get_gallery_photos(db, location.id, location.is_paid)

    return LocationOut(
        id=location.id,
        brand_id=location.brand_id,
        location_name=location.location_name,
        address_line1=location.address_line1,
        address_line2=location.address_line2,
        city=location.city,
        state=location.state,
        postal_code=location.postal_code,
        country=location.country,
        phone=location.phone,
        timezone=location.timezone,
        latitude=float(location.latitude) if location.latitude is not None else None,
        longitude=float(location.longitude) if location.longitude is not None else None,
        is_verified=location.is_verified,
        is_paid=location.is_paid,
        is_open_now=is_open_now,
        hours=[
            HoursOut(
                day_of_week=row.day_of_week,
                open_time=row.open_time,
                close_time=row.close_time,
                is_closed=row.is_closed,
            )
            for row in hours_rows
        ],
        cover_photo_url=s3_service.resolve_media_url(cover.s3_key) if cover else None,
        gallery_photos=[
            GalleryPhotoOut(
                id=photo.id,
                url=s3_service.resolve_media_url(photo.s3_key),
                display_order=photo.display_order,
            )
            for photo in gallery
        ],
    )


async def get_location(db: AsyncSession, location_id: int) -> LocationOut:
    location = await db.get(RestaurantLocation, location_id)
    if location is None:
        raise AppError(404, "Location not found", "not_found")
    return await _location_to_out(db, location)


async def get_location_or_404(db: AsyncSession, location_id: int) -> RestaurantLocation:
    location = await db.get(RestaurantLocation, location_id)
    if location is None:
        raise AppError(404, "Location not found", "not_found")
    return location


async def create_location(db: AsyncSession, body: LocationCreate, current_user) -> LocationOut:
    brand = await db.get(RestaurantBrand, body.brand_id)
    if brand is None:
        raise AppError(404, "Restaurant not found", "not_found")

    owner = await auth_service.get_owner_account_by_sub(db, current_user.cognito_sub)
    if owner is None or brand.owner_id != owner.id:
        raise AppError(403, "Not authorized to add a location to this restaurant", "forbidden")

    location = RestaurantLocation(
        brand_id=body.brand_id,
        address_line1=body.address_line1,
        address_line2=body.address_line2,
        city=body.city,
        state=body.state.upper(),
        postal_code=body.postal_code,
        country=body.country.upper(),
        phone=body.phone,
        timezone=body.timezone,
        latitude=_to_decimal(body.latitude),
        longitude=_to_decimal(body.longitude),
        is_paid=False,
        is_verified=False,
        is_active=True,
    )
    db.add(location)
    await db.flush()

    if body.latitude is not None and body.longitude is not None:
        await _sync_geom(db, location.id, body.latitude, body.longitude)

    await audit_service.log(
        db,
        table_name="restaurant_location",
        record_id=location.id,
        action="create",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=None,
        new_val={
            "brand_id": location.brand_id,
            "address_line1": location.address_line1,
            "city": location.city,
            "state": location.state,
        },
    )
    await db.commit()
    return await get_location(db, location.id)


_UPDATABLE_FIELDS = (
    "location_name",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "postal_code",
    "country",
    "phone",
    "timezone",
)


async def update_location(
    db: AsyncSession, location_id: int, body: LocationUpdate, current_user
) -> LocationOut:
    location = await get_location_or_404(db, location_id)

    old_val = {field: getattr(location, field) for field in _UPDATABLE_FIELDS}
    old_val["latitude"] = float(location.latitude) if location.latitude is not None else None
    old_val["longitude"] = float(location.longitude) if location.longitude is not None else None

    data = body.model_dump(exclude_unset=True)
    for field in _UPDATABLE_FIELDS:
        if field in data and data[field] is not None:
            value = data[field]
            if field in ("state", "country"):
                value = value.upper()
            setattr(location, field, value)

    lat_changed = "latitude" in data and data["latitude"] is not None
    lng_changed = "longitude" in data and data["longitude"] is not None
    if lat_changed:
        location.latitude = _to_decimal(data["latitude"])
    if lng_changed:
        location.longitude = _to_decimal(data["longitude"])

    await db.flush()

    if lat_changed or lng_changed:
        lat = float(location.latitude) if location.latitude is not None else None
        lng = float(location.longitude) if location.longitude is not None else None
        if lat is not None and lng is not None:
            await _sync_geom(db, location.id, lat, lng)

    new_val = {field: getattr(location, field) for field in _UPDATABLE_FIELDS}
    new_val["latitude"] = float(location.latitude) if location.latitude is not None else None
    new_val["longitude"] = float(location.longitude) if location.longitude is not None else None

    await audit_service.log(
        db,
        table_name="restaurant_location",
        record_id=location.id,
        action="update",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=old_val,
        new_val=new_val,
    )
    await db.commit()
    return await get_location(db, location.id)


async def delete_location(db: AsyncSession, location_id: int, current_user) -> None:
    """Soft delete — sets is_active=false (docs/API_CONTRACTS.md "DELETE
    /locations/{id}"). Nothing is actually removed.
    """
    location = await get_location_or_404(db, location_id)
    old_val = {"is_active": location.is_active}
    location.is_active = False
    new_val = {"is_active": location.is_active}
    await audit_service.log(
        db,
        table_name="restaurant_location",
        record_id=location.id,
        action="update",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=old_val,
        new_val=new_val,
    )
    await db.commit()


async def list_locations_for_brand(
    db: AsyncSession, brand_id: int, pagination
) -> LocationListResponse:
    brand = await db.get(RestaurantBrand, brand_id)
    if brand is None:
        raise AppError(404, "Restaurant not found", "not_found")

    base_filter = (RestaurantLocation.brand_id == brand_id, RestaurantLocation.is_active == True)  # noqa: E712

    total = (
        await db.execute(select(func.count()).select_from(RestaurantLocation).where(*base_filter))
    ).scalar_one()

    rows = (
        await db.execute(
            select(RestaurantLocation)
            .where(*base_filter)
            .order_by(RestaurantLocation.id)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    ).scalars().all()

    results = []
    for row in rows:
        is_open_now = await hours_service.is_open_now_for_location(db, row.id, row.timezone)
        results.append(
            LocationSummaryOut(
                id=row.id,
                location_name=row.location_name,
                address_line1=row.address_line1,
                city=row.city,
                state=row.state,
                postal_code=row.postal_code,
                phone=row.phone,
                is_verified=row.is_verified,
                is_paid=row.is_paid,
                is_open_now=is_open_now,
            )
        )

    return LocationListResponse(
        results=results, page=pagination.page, page_size=pagination.page_size, total=total
    )


# ---------------------------------------------------------------------------
# Hours sub-resource
# ---------------------------------------------------------------------------


async def replace_location_hours(
    db: AsyncSession, location_id: int, entries: list[HourEntryIn], current_user
) -> HoursResponse:
    location = await get_location_or_404(db, location_id)
    await hours_service.replace_hours(db, location.id, entries)

    await audit_service.log(
        db,
        table_name="restaurant_location",
        record_id=location.id,
        action="update",
        actor_id=current_user.cognito_sub,
        actor_role=current_user.role,
        old_val=None,
        new_val={"hours_updated_days": [e.day_of_week for e in entries]},
    )
    await db.commit()

    rows = await hours_service.get_hours_for_location(db, location.id)
    return HoursResponse(
        hours=[
            HoursOut(
                day_of_week=row.day_of_week,
                open_time=row.open_time,
                close_time=row.close_time,
                is_closed=row.is_closed,
            )
            for row in rows
        ]
    )


# ---------------------------------------------------------------------------
# Photos sub-resource — restaurant_photo is not in the audit-required
# table list (docs/API_CONTRACTS.md), so no audit_log write below.
# ---------------------------------------------------------------------------


async def create_photo_upload_url(
    db: AsyncSession, location_id: int, content_type: str
) -> UploadUrlResponse:
    await get_location_or_404(db, location_id)
    url, key, expires_in = s3_service.generate_location_photo_upload_url(location_id, content_type)
    return UploadUrlResponse(upload_url=url, s3_key=key, expires_in=expires_in)


async def create_location_photo(
    db: AsyncSession, location_id: int, body: PhotoCreate, current_user
) -> PhotoOut:
    location = await get_location_or_404(db, location_id)
    photo = await photo_service.create_photo(db, location, body, current_user.cognito_sub)
    return photo_service.to_photo_out(photo)


async def update_location_photo(
    db: AsyncSession, location_id: int, photo_id: int, body: PhotoUpdate
) -> PhotoOut:
    location = await get_location_or_404(db, location_id)
    photo = await photo_service.update_photo(db, location, photo_id, body)
    return photo_service.to_photo_out(photo)


async def delete_location_photo(db: AsyncSession, location_id: int, photo_id: int) -> None:
    location = await get_location_or_404(db, location_id)
    await photo_service.delete_photo(db, location, photo_id)

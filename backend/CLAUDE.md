# Backend Dev Agent

> First read the root `/CLAUDE.md` — it contains shared context, stack, and
> universal guardrails that apply to this agent too.

## Role
You are the Backend Dev agent for the Restaurant Discovery Platform.
You own everything in `/backend`. You build and maintain the FastAPI application,
Lambda handlers, database models, Alembic migrations, and Stripe webhook handlers.
You do NOT touch `/frontend`, `/infra`, or `/tests` unless explicitly told to.

## Directory Structure
```
/backend
  /app
    main.py               ← FastAPI app entry point + Mangum handler
    /routers              ← one file per resource (restaurants.py, search.py, etc.)
    /models               ← SQLAlchemy models (one file per entity group)
    /schemas              ← Pydantic v2 request/response schemas
    /services             ← business logic (one file per domain)
    /dependencies         ← FastAPI deps (auth, db session, is_paid check)
    /db
      session.py          ← async SQLAlchemy engine + session factory
      base.py             ← declarative base
  /migrations             ← Alembic migration files
    alembic.ini
    /versions
  requirements.txt
  requirements-dev.txt
  Dockerfile              ← for local dev only; Lambda uses zip deployment
```

## Stack
- Python 3.12
- FastAPI 0.111+
- SQLAlchemy 2.x (async, with asyncpg driver)
- Alembic 1.13+
- Pydantic v2
- Mangum 0.17+ (wraps FastAPI for Lambda)
- boto3 (S3 presigned URLs, SES)
- stripe 8.x
- GeoAlchemy2 (PostGIS types for SQLAlchemy)
- pytest + pytest-asyncio (tests go in /tests, not here)

## Key Patterns

### Endpoint structure
```python
# /backend/app/routers/restaurants.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user, require_owner
from app.dependencies.db import get_db
from app.services.restaurant_service import RestaurantService
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.post("/", response_model=RestaurantResponse, status_code=201)
async def create_restaurant(
    body: RestaurantCreate,
    db=Depends(get_db),
    current_user=Depends(require_owner),
):
    return await RestaurantService(db).create(body, owner_id=current_user.id)
```

### is_paid() check — ALWAYS use this before returning paid content
```python
# /backend/app/dependencies/tier.py
async def require_paid_location(location_id: int, db=Depends(get_db)):
    result = await db.execute(
        select(RestaurantLocation.is_paid)
        .where(RestaurantLocation.id == location_id)
    )
    is_paid = result.scalar_one_or_none()
    if not is_paid:
        raise HTTPException(status_code=403, detail="Paid tier required")
    return True
```

### Manager permission check — ALWAYS validate server-side
```python
# /backend/app/dependencies/auth.py
async def require_location_access(
    location_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Owners have implicit access to all their locations
    if current_user.role == "owner":
        location = await db.get(RestaurantLocation, location_id)
        brand = await db.get(RestaurantBrand, location.brand_id)
        if brand.owner_id != current_user.id:
            raise HTTPException(status_code=403)
        return True
    # Managers must have explicit assignment
    result = await db.execute(
        select(LocationManager)
        .where(
            LocationManager.user_id == current_user.id,
            LocationManager.location_id == location_id,
            LocationManager.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not assigned to this location")
    return True
```

### Audit log — ALWAYS write for mutations on core entities
```python
# /backend/app/services/audit_service.py
async def log(db, table_name, record_id, action, actor_id, actor_role, old_val=None, new_val=None):
    entry = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,          # "create" | "update" | "delete"
        actor_id=actor_id,
        actor_role=actor_role,
        old_val=old_val,        # JSON dict or None
        new_val=new_val,        # JSON dict or None
    )
    db.add(entry)
    # Do not commit here — caller commits as part of the same transaction
```

### Geo search pattern (PostGIS)
```python
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID

# Find locations within 15 miles (24140 metres) of a point
results = await db.execute(
    select(RestaurantLocation)
    .where(
        ST_DWithin(
            RestaurantLocation.geom,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326),
            24140,  # 15 miles in metres
        )
    )
    .where(RestaurantLocation.is_active == True)
    .order_by(RestaurantLocation.geom.distance_centroid(
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    ))
)
```

### Stripe webhook handler
```python
# /backend/app/routers/webhooks.py
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400)

    if event["type"] == "invoice.paid":
        await handle_invoice_paid(event["data"]["object"], db)
    elif event["type"] == "invoice.payment_failed":
        await handle_invoice_failed(event["data"]["object"], db)
    return {"status": "ok"}

async def handle_invoice_failed(invoice, db):
    # Set is_paid=false for ALL locations on this owner's subscription
    sub_id = invoice["subscription"]
    owner = await db.execute(select(OwnerAccount).where(OwnerAccount.stripe_sub_id == sub_id))
    owner = owner.scalar_one()
    await db.execute(
        update(RestaurantLocation)
        .where(RestaurantLocation.brand_id.in_(
            select(RestaurantBrand.id).where(RestaurantBrand.owner_id == owner.id)
        ))
        .values(is_paid=False, paid_until=None)
    )
    await db.commit()
    # TODO: send email via SES (Phase 2)
```

### S3 presigned URL generation
```python
import boto3
from botocore.config import Config

s3 = boto3.client("s3", config=Config(signature_version="s3v4"))

def generate_upload_url(bucket: str, key: str, content_type: str) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=600,  # 10 minutes
    )
# Never accept file uploads directly through Lambda — always presigned URL
```

## Public Routes (no Cognito authorizer required)
These routes are explicitly public — all others require auth:
- `GET /health`
- `GET /search`
- `GET /restaurants/{id}`
- `GET /restaurants/{id}/locations`
- `GET /locations/{id}`

## Environment Variables (never hardcode these)
```
DATABASE_URL          Aurora connection string (from Secrets Manager)
STRIPE_SECRET_KEY     Stripe API key
STRIPE_WEBHOOK_SECRET Stripe webhook signing secret
S3_MEDIA_BUCKET       Media bucket name
SES_FROM_ADDRESS      Platform from email
JWT_SECRET            Cognito JWT public key (fetched from Cognito endpoint)
```

## Phase 1 Scope — What to Build Now
- DB models: owner_account, restaurant_brand, restaurant_location, cuisine_tag,
  restaurant_cuisine, location_manager, user_follow, audit_log, platform_pricing, admin_free_offer
- Endpoints: /search, /restaurants (CRUD), /locations (CRUD), /claim, /auth
- PostGIS geo search with filters (cuisine, dietary, type, open_now)
- Claim flow backend (submit, admin review, approve/reject)
- Owner portal endpoints (free tier: edit basic info, hours, cover photo)
- Open/closed status based on hours JSONB + timezone

## Phase 1 — Do NOT Build Yet
- Stripe checkout, webhooks, subscription management (Phase 2)
- Menu CRUD, deals engine, deal alerts (Phase 2)
- Analytics endpoints (Phase 2)
- Natural language search, Claude API integration (Phase 3)
- orchestrator.py (Phase 3)

## Guardrails (Backend-Specific)

### NEVER
- NEVER return paid content (menus, deals) without checking `is_paid`
- NEVER trust JWT claims for manager location access — always query `location_manager` table
- NEVER run raw `ALTER TABLE` SQL — always use Alembic migrations
- NEVER expose stack traces or internal error details in API responses
- NEVER store passwords — Cognito handles all auth
- NEVER call the Stripe API in the request path (use webhooks + async jobs)
- NEVER skip the audit_log for writes on: restaurant_brand, restaurant_location,
  menu_item, deal, owner_account, location_manager

### ALWAYS
- ALWAYS validate that the authenticated user has rights to the resource being modified
- ALWAYS return consistent error shapes: `{"detail": "...", "code": "..."}`
- ALWAYS use database transactions for multi-step writes
- ALWAYS include pagination on list endpoints (default: 20, max: 100)

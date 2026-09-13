"""cuisine_tag endpoints. See docs/API_CONTRACTS.md "GET /cuisine-tags".

Public read list — no Cognito authorizer required (backend/CLAUDE.md
"Public Routes"). No write API here: `cuisine_tag` is admin-seeded only
(see app/models/cuisine_tag.py, app/services/cuisine_service.py).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.cuisine import CuisineCategory, CuisineTagListResponse, CuisineTagOut
from app.services import cuisine_service

router = APIRouter(prefix="/cuisine-tags", tags=["cuisine-tags"])


@router.get("", response_model=CuisineTagListResponse)
async def list_cuisine_tags(
    category: CuisineCategory | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> CuisineTagListResponse:
    """Auth: none (public). Optional `category` filter; `is_active=true`
    rows only; no pagination (docs/API_CONTRACTS.md "GET /cuisine-tags")."""
    tags = await cuisine_service.list_active_cuisine_tags(db, category)
    return CuisineTagListResponse(results=[CuisineTagOut.model_validate(t) for t in tags])

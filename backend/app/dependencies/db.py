"""DB session FastAPI dependency.

Thin wrapper around `app.db.session.get_session` (Architect/DB-layer owned)
so routers/services depend on `get_db` per backend/CLAUDE.md's documented
pattern (`db=Depends(get_db)`) rather than importing the session module
directly everywhere.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session

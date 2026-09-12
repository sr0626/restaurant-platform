"""Async SQLAlchemy engine + session factory.

Reads `DATABASE_URL` from the environment — never hardcode a connection
string here (see root `CLAUDE.md` "Environment Variables" and "NEVER —
Security"). In deployed environments this value is populated from AWS
Secrets Manager into the Lambda's environment; locally it comes from a
gitignored `.env` file.

Expected form (asyncpg driver, required for SQLAlchemy 2.x async):
    postgresql+asyncpg://<user>:<password>@<host>:5432/<db>

Backend Dev's `app/dependencies/db.py::get_db` should depend on
`get_session()` below rather than re-implementing session management.
"""
import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it in the environment (or a "
            "local .env, gitignored) before creating the engine — see "
            "root CLAUDE.md 'Environment Variables'."
        )
    return url


# Engine is created lazily on first use, not at import time, so that
# importing this module (e.g. from Alembic tooling or tests that patch
# the URL) never fails just because DATABASE_URL isn't set yet.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            echo=False,
            pool_pre_ping=True,
            # Aurora Serverless v2 scales to zero (min_capacity=0) — keep
            # the pool small so we don't hold connections open against a
            # scaled-down instance (see root CLAUDE.md cost guardrails).
            pool_size=5,
            max_overflow=5,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session, closes it after the request."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

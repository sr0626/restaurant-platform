"""Async SQLAlchemy engine + session factory.

Reads `DATABASE_URL` from the environment — never hardcode a connection
string here (see root `CLAUDE.md` "Environment Variables" and "NEVER —
Security"). Locally, `DATABASE_URL` comes from a gitignored `.env` file.

The real deployed Lambda does NOT set `DATABASE_URL` directly — per root
`CLAUDE.md` / `infra/CLAUDE.md` "Secrets Management" ("ALL secrets stored in
AWS Secrets Manager — never in environment variables directly. Lambda reads
secrets at cold start via boto3 `get_secret_value`"), Terraform's Lambda
module (`infra/modules/lambda/main.tf`) only sets `DB_SECRET_NAME` — the
Secrets Manager secret *name* holding DB credentials. So when `DATABASE_URL`
isn't set but `DB_SECRET_NAME` is, we fetch the secret once at cold start
and build the connection URL from it. The secret's JSON shape (see
`infra/modules/aurora/main.tf` `aws_secretsmanager_secret_version.db`):
    {"username": ..., "password": ..., "host": ..., "port": 5432,
     "dbname": "restaurantdb", "engine": "aurora-postgresql"}

Expected final URL form (asyncpg driver, required for SQLAlchemy 2.x async):
    postgresql+asyncpg://<user>:<password>@<host>:5432/<db>

Backend Dev's `app/dependencies/db.py::get_db` should depend on
`get_session()` below rather than re-implementing session management.
"""
import json
import os
from collections.abc import AsyncGenerator
from urllib.parse import quote_plus

import boto3
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Cached across warm invocations of the same Lambda execution environment —
# fetched from Secrets Manager at most once per cold start, never per
# request (see module docstring; same cold-start-only caching pattern as
# `app/services/s3_service.py`'s lazy client singleton).
_database_url_from_secret: str | None = None


def _build_url_from_secret(secret_name: str) -> str:
    global _database_url_from_secret
    if _database_url_from_secret is None:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        user = quote_plus(secret["username"])
        password = quote_plus(secret["password"])
        host = secret["host"]
        port = secret.get("port", 5432)
        dbname = secret["dbname"]
        _database_url_from_secret = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
        )
    return _database_url_from_secret


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    secret_name = os.environ.get("DB_SECRET_NAME")
    if secret_name:
        return _build_url_from_secret(secret_name)

    raise RuntimeError(
        "DATABASE_URL is not set, and DB_SECRET_NAME is not set either. "
        "Set DATABASE_URL in the environment (or a local .env, gitignored) "
        "for local dev, or DB_SECRET_NAME (Secrets Manager secret name) in "
        "deployed environments — see root CLAUDE.md 'Environment Variables' "
        "and infra/CLAUDE.md 'Secrets Management'."
    )


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

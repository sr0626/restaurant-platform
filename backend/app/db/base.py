"""SQLAlchemy 2.x async declarative base.

Every ORM model in `app/models/` inherits from `Base`. Alembic's
`migrations/env.py` imports `Base.metadata` (via `app.models`, which
imports every model module) as the single source of truth for
autogenerate.

Owned by the Architect agent — see `architect/CLAUDE.md`. Backend Dev
consumes this module but does not own schema/model definitions.
"""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for every model in the app."""


class TimestampMixin:
    """Adds `created_at` / `updated_at` columns.

    Applied selectively — not every Phase 1 table needs both. For
    example `audit_log` is append-only and defines its own single
    `created_at` column rather than using this mixin.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

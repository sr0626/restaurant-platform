"""Apply already-reviewed Alembic migrations to the real deployed database.

This does NOT design or generate migrations -- root CLAUDE.md's "NEVER run
Alembic migrations -- generate migration files only" is about agents never
executing `alembic upgrade` themselves against real AWS. This module is the
mechanism that lets the HUMAN do that explicitly, the same trust boundary as
`terraform apply` or any other direct AWS action in this repo: only someone
who already holds `lambda:InvokeFunction` on this one function can reach it
at all (see `app/scripts/management.py`'s module docstring), and invoking it
is the human's own per-command-approved `aws lambda invoke` call, never
something run automatically or by an agent.

Reuses `app.db.session._get_database_url()` for the connection string
(DATABASE_URL if set, else the DB_SECRET_NAME-derived one -- same
resolution used everywhere else) rather than re-deriving it, so this can
never drift from what the running app actually connects to.

migrations/ has to actually be present in the image for this to work --
see backend/Dockerfile, which now COPYs it alongside app/.
"""
from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.db.session import _get_database_url


def run_upgrade(revision: str = "head") -> dict:
    """Runs `alembic upgrade <revision>` against the real database.

    Sets DATABASE_URL in the environment first (rather than passing the URL
    through some other channel) because that's exactly what
    migrations/env.py already reads -- keeps this a thin wrapper around the
    same tool a human would run locally, not a reimplementation of it.
    """
    database_url = _get_database_url()
    os.environ["DATABASE_URL"] = database_url

    migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
    cfg = Config(str(migrations_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(migrations_dir))

    command.upgrade(cfg, revision)

    return {"revision": revision}

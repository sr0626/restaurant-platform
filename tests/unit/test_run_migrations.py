"""Unit test: `app/scripts/run_migrations.py`'s alembic-upgrade wrapper.

Never touches a real database or runs a real migration -- `alembic.command.
upgrade` is monkeypatched to a stub that just records what it was called
with, mirroring tests/unit/test_db_session_secrets.py's approach of
stubbing the external call rather than exercising it for real.
"""
from __future__ import annotations

import pytest

from app.scripts import run_migrations


def test_run_upgrade_sets_database_url_and_calls_alembic_upgrade(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        run_migrations, "_get_database_url", lambda: "postgresql+asyncpg://u:p@h:5432/db"
    )

    calls: list[tuple] = []
    monkeypatch.setattr(
        run_migrations.command, "upgrade", lambda cfg, rev: calls.append((cfg, rev))
    )

    result = run_migrations.run_upgrade("head")

    assert result == {"revision": "head"}
    assert calls[0][1] == "head"
    assert __import__("os").environ["DATABASE_URL"] == "postgresql+asyncpg://u:p@h:5432/db"


def test_run_upgrade_defaults_to_head(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(run_migrations, "_get_database_url", lambda: "postgresql+asyncpg://u:p@h:5432/db")

    calls: list[tuple] = []
    monkeypatch.setattr(
        run_migrations.command, "upgrade", lambda cfg, rev: calls.append((cfg, rev))
    )

    run_migrations.run_upgrade()

    assert calls[0][1] == "head"


def test_run_upgrade_points_config_at_the_real_migrations_dir(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(run_migrations, "_get_database_url", lambda: "postgresql+asyncpg://u:p@h:5432/db")

    captured_cfg = {}

    def _fake_upgrade(cfg, rev):
        captured_cfg["script_location"] = cfg.get_main_option("script_location")

    monkeypatch.setattr(run_migrations.command, "upgrade", _fake_upgrade)

    run_migrations.run_upgrade("head")

    assert captured_cfg["script_location"].endswith("backend/migrations") or captured_cfg[
        "script_location"
    ].endswith("backend\\migrations")

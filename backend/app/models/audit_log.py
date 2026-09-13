"""audit_log — append-only write history for core entities.

Root CLAUDE.md "ALWAYS — Quality": an audit_log entry is required for
every write on restaurant_brand, restaurant_location, menu_item, deal,
owner_account, location_manager. (menu_item/deal don't exist yet in
Phase 1 — the table is generic via `table_name` + `record_id` so it
already supports them without a schema change when Phase 2 adds them.)

Column names/shape match backend/CLAUDE.md's
`app/services/audit_service.py::log()` exactly — this table is that
function's write target.

`record_id` is intentionally a plain BigInteger, not a real foreign
key: it's polymorphic across every audited table, so no single FK
target applies.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_table_record", "table_name", "record_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # "create" | "update" | "delete"
    action: Mapped[str] = mapped_column(String(16), nullable=False)

    # Cognito `sub` (or, for system/admin actions, an admin identifier).
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # "owner" | "manager" | "admin"
    actor_role: Mapped[str] = mapped_column(String(16), nullable=False)

    old_val: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_val: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog table={self.table_name} record_id={self.record_id} "
            f"action={self.action}>"
        )

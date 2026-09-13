"""location_manager — owner-assigned manager access to a location.

JUDGMENT CALL (flagged for review): `user_id` stores the manager's
Cognito `sub` directly rather than a foreign key to a local "manager
account" table — no such table appears in the Phase 1 entity list, and
Cognito (user pool group "manager") is the identity source of truth for
managers per root CLAUDE.md. If a local manager profile table is added
later, this column becomes a natural FK target.

Schema shape supports the "max 2 active managers per location on paid
tier" rule (DECISIONS.md "Assignable location managers capped at 2")
without enforcing it here — enforcement is Backend Dev's job at the
service layer (root/backend CLAUDE.md), checked on every write against
`is_active=true` rows for the location:
    SELECT count(*) FROM location_manager
    WHERE location_id = :id AND is_active = true
- `ix_location_manager_location_active` makes that count cheap.
- `uq_location_manager_active_user` is a data-integrity backstop (a
  user can't hold two simultaneous active assignment rows on the same
  location) — it is NOT the cap itself, which is a count, not a
  uniqueness rule, and stays Backend Dev's to enforce.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.owner_account import OwnerAccount
    from app.models.restaurant_location import RestaurantLocation


class LocationManager(TimestampMixin, Base):
    __tablename__ = "location_manager"
    __table_args__ = (
        Index(
            "uq_location_manager_active_user",
            "location_id",
            "user_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "ix_location_manager_location_active",
            "location_id",
            "is_active",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    location_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_location.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Cognito `sub` of the manager — see JUDGMENT CALL note above.
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Owner who made the assignment (for audit/attribution — the write
    # itself is also recorded in audit_log per root CLAUDE.md).
    assigned_by_owner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("owner_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    location: Mapped["RestaurantLocation"] = relationship(back_populates="managers")
    assigned_by: Mapped["OwnerAccount | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LocationManager location_id={self.location_id} "
            f"user_id={self.user_id!r} active={self.is_active}>"
        )

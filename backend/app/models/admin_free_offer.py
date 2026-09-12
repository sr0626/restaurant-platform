"""admin_free_offer — admin-granted free-tier window, owner-scoped.

DECISIONS.md "Admin free offer sets is_paid=true + paid_until directly":
no Stripe interaction — a simple DB write. DECISIONS.md "Owner-scoped
free offer covers all their locations including new ones added during
the offer": the grant is scoped to the owner (this table), not to a
fixed list of locations, so the service layer applies it to *all* of
the owner's locations, including ones added mid-offer.

This table is the record of the *grant*; the actual `is_paid=true` /
`paid_until=end_date` writes on each of the owner's restaurant_location
rows are Backend Dev's service-layer job (root/backend CLAUDE.md), not
modeled again here.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.owner_account import OwnerAccount


class AdminFreeOffer(TimestampMixin, Base):
    __tablename__ = "admin_free_offer"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("owner_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Admin (Cognito sub) who granted the offer.
    granted_by: Mapped[str] = mapped_column(String(64), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lets admin revoke early without deleting the historical grant row
    # (root CLAUDE.md "NEVER delete or truncate any DB table").
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped["OwnerAccount"] = relationship(back_populates="free_offers")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AdminFreeOffer owner_id={self.owner_id} "
            f"{self.start_date}..{self.end_date}>"
        )

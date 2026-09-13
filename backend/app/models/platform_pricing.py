"""platform_pricing — admin-configurable per-location pricing.

DECISIONS.md "Pricing stored in platform_pricing table with effective
dates": admin can set a new price with a future `effective_date`; the
system reads the most recent row where `effective_date <= today`. No
code deploy needed for price changes. Current pricing: $100/mo or
$1,000/yr per location (root CLAUDE.md "Billing model").
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformPricing(Base):
    __tablename__ = "platform_pricing"
    __table_args__ = (
        Index("ix_platform_pricing_effective_date", "effective_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    yearly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Row becomes effective on this date; the current price is the row
    # with the latest effective_date <= today.
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Admin (Cognito sub) who created this pricing row, for audit context.
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PlatformPricing effective_date={self.effective_date} "
            f"monthly={self.monthly_price}>"
        )

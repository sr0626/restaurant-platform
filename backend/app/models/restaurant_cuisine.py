"""restaurant_cuisine — join table between restaurant_brand and cuisine_tag.

JUDGMENT CALL (not settled in root CLAUDE.md / DECISIONS.md — flagged
for review): tagged at the **brand** level, not per-location. A brand's
regional/dietary/type/signature tags are treated as describing the
restaurant concept as a whole (same menu style across its locations),
which also matches DECISIONS.md "Brand-level search results (not flat
location results)" — search filters and result cards operate on the
brand. If a real multi-location brand ever needs per-location cuisine
variance, this join would need to move to (or add) location_id.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cuisine_tag import CuisineTag
    from app.models.restaurant_brand import RestaurantBrand


class RestaurantCuisine(Base):
    __tablename__ = "restaurant_cuisine"
    __table_args__ = (
        UniqueConstraint("brand_id", "cuisine_tag_id", name="uq_restaurant_cuisine_brand_tag"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    brand_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_brand.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cuisine_tag_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cuisine_tag.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    brand: Mapped["RestaurantBrand"] = relationship(back_populates="cuisines")
    cuisine_tag: Mapped["CuisineTag"] = relationship(back_populates="brand_links")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RestaurantCuisine brand_id={self.brand_id} cuisine_tag_id={self.cuisine_tag_id}>"

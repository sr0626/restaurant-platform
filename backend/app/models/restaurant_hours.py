"""restaurant_hours — structured weekly operating hours per location.

DECISIONS.md "Restaurant hours": captured at seed time so it isn't a
later schema migration. `is_closed` is nullable by design — NULL means
"hours unknown, call ahead" for locations without confirmed hours at
seed time, rather than a guessed value. True open/closed *display*
status (per root CLAUDE.md domain model / DECISIONS.md) is computed by
Backend Dev's service layer from (day_of_week, open_time, close_time,
is_closed) + `restaurant_location.timezone` — not stored here.

JUDGMENT CALL (flagged for review): `day_of_week` convention is
0=Monday .. 6=Sunday (ISO-style weekday numbering), chosen for
consistency with Python's `date.weekday()`. Not stated in
DECISIONS.md — Backend Dev should confirm this convention before
seeding data or computing "open now" against it.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    SmallInteger,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant_location import RestaurantLocation


class RestaurantHours(TimestampMixin, Base):
    __tablename__ = "restaurant_hours"
    __table_args__ = (
        UniqueConstraint(
            "location_id", "day_of_week", name="uq_restaurant_hours_location_day"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    location_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_location.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 0=Monday .. 6=Sunday — see JUDGMENT CALL note above.
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # True = closed all day. False = open (per open_time/close_time).
    # NULL = hours unknown for this day (never guessed at seed time).
    is_closed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    location: Mapped["RestaurantLocation"] = relationship(back_populates="hours")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RestaurantHours location_id={self.location_id} "
            f"day={self.day_of_week} closed={self.is_closed}>"
        )

"""PUT /locations/{id}/hours — see docs/API_CONTRACTS.md."""
from __future__ import annotations

from datetime import time

from pydantic import BaseModel, field_validator

from app.schemas.location import HoursOut


class HourEntryIn(BaseModel):
    day_of_week: int
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool | None = None

    @field_validator("day_of_week")
    @classmethod
    def _validate_day(cls, value: int) -> int:
        # 0=Monday .. 6=Sunday — docs/DATA_MODEL.md judgment-call note,
        # matches Python's date.weekday().
        if not 0 <= value <= 6:
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        return value


class HoursReplaceRequest(BaseModel):
    hours: list[HourEntryIn]


class HoursResponse(BaseModel):
    hours: list[HoursOut]

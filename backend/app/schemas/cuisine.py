from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CuisineTagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    display_name: str
    category: str

"""Shared pagination dependency for every list endpoint.

backend/CLAUDE.md "ALWAYS include pagination on list endpoints (default: 20,
max: 100)".
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)

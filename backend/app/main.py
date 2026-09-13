"""FastAPI app entry point + Mangum Lambda handler.

Deployed as a Lambda container image (root CLAUDE.md "Containerization") —
`backend/Dockerfile`'s `CMD ["app.main.handler"]` points here. Locally,
run with `uvicorn app.main:app --reload` from `backend/` instead of
invoking `handler` directly.
"""
from __future__ import annotations

from fastapi import FastAPI
from mangum import Mangum

from app.core.errors import register_exception_handlers
from app.routers import auth, claim, cuisine, health, locations, restaurants, search

app = FastAPI(title="Restaurant Discovery Platform API")

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(restaurants.router)
app.include_router(locations.router)
app.include_router(claim.router)
app.include_router(auth.router)
app.include_router(cuisine.router)

# package_type = "Image" Lambda functions have no separate "handler" config
# — the Dockerfile's CMD *is* the handler, in "<module>.<callable>" form
# (infra/CLAUDE.md "Lambda + API Gateway"). `handler` is that callable.
handler = Mangum(app)

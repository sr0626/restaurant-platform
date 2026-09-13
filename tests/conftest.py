"""Root pytest fixtures — shared by /tests/unit and /tests/integration.

Test Data Principles (tests/CLAUDE.md): never production data/credentials,
always factories (never hardcoded IDs), always mock AWS instead of hitting
real S3/Cognito.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `import app...` (the backend package) resolve without needing
# backend/ on PYTHONPATH externally — QA owns /tests only, backend/app is
# read-only from here (never modified).
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Required env vars must exist before app.dependencies.auth / app.db.session
# are imported (they read os.environ at call time, not import time, but set
# them up-front anyway so every test starts from the same known-fake config).
# NEVER real credentials/endpoints (tests/CLAUDE.md "NEVER use production
# database, credentials").
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("COGNITO_USER_POOL_ID", "us-east-1_testpool")
os.environ.setdefault("COGNITO_REGION", "us-east-1")
os.environ.setdefault("S3_MEDIA_BUCKET", "test-media-bucket")
os.environ.setdefault("MEDIA_CDN_DOMAIN", "media.test.example.com")

import pytest  # noqa: E402

# NOTE on "no real AWS/network" enforcement: rather than a global socket
# block (risky — asyncio/anyio use real sockets internally for event-loop
# self-pipes on some platforms, and that breaks pytest-asyncio itself), each
# fixture that would otherwise touch AWS is individually stubbed:
#   - app.services.s3_service._get_s3_client() -> fake_s3_client fixture
#     (tests/unit/test_s3_service.py, tests/integration/conftest.py)
#   - app.dependencies.auth._get_jwk_client() -> local RSA keypair fixture
#     (tests/unit/test_auth_jwt.py)
#   - app.dependencies.auth.get_current_user -> FastAPI dependency_override
#     with a fake CurrentUser (tests/integration/conftest.py) so integration
#     tests never verify a real JWT or fetch a real JWKS document at all.
# DATABASE_URL above is also never a real, reachable database — integration
# tests override app.dependencies.db.get_db with a local SQLite/aiosqlite
# session instead of ever calling app.db.session.get_session().

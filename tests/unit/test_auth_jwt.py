"""Unit test: Cognito JWT verification in `app/dependencies/auth.py` — the
JWKS fetch itself is fully mocked (root CLAUDE.md AWS Best Practices /
tests/CLAUDE.md "ALWAYS mock AWS calls"): `_get_jwk_client()` is
monkeypatched to a fake object backed by a locally generated RSA keypair, so
no real HTTP request to Cognito's `.well-known/jwks.json` endpoint is ever
made. Everything else — RS256 signature verification, issuer check,
token_use check, `cognito:groups` -> role extraction, missing/malformed
bearer token handling — is the real code path in
`app.dependencies.auth._decode_token` / `get_current_user`.
"""
from __future__ import annotations

import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.errors import AppError
from app.dependencies import auth as auth_deps


@pytest.fixture(scope="module")
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


@pytest.fixture(scope="module")
def other_rsa_keypair():
    """A second, unrelated keypair — used to prove a token signed by an
    attacker/foreign key is rejected (signature won't match what the
    "JWKS" fake resolves to).
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKClient:
    """Stands in for `jwt.PyJWKClient` — never performs the real HTTPS GET
    against Cognito's JWKS endpoint.
    """

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(self._public_key)


@pytest.fixture(autouse=True)
def mock_jwks(monkeypatch: pytest.MonkeyPatch, rsa_keypair):
    _private, public_key = rsa_keypair
    monkeypatch.setattr(auth_deps, "_get_jwk_client", lambda: _FakeJWKClient(public_key))


def _issuer() -> str:
    return f"https://cognito-idp.{auth_deps._region()}.amazonaws.com/{auth_deps._user_pool_id()}"


def _issue_token(
    private_key,
    *,
    sub: str | None = None,
    groups: list[str] | None = None,
    email: str | None = "user@example.com",
    token_use: str = "id",
    issuer: str | None = None,
    extra_claims: dict | None = None,
) -> str:
    claims = {
        "sub": sub if sub is not None else str(uuid.uuid4()),
        "iss": issuer if issuer is not None else _issuer(),
        "token_use": token_use,
    }
    if email is not None:
        claims["email"] = email
    if groups is not None:
        claims["cognito:groups"] = groups
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, private_key, algorithm="RS256")


@pytest.mark.asyncio
async def test_valid_owner_token_resolves_role_and_identity(rsa_keypair):
    private_key, _ = rsa_keypair
    sub = str(uuid.uuid4())
    token = _issue_token(private_key, sub=sub, groups=["owner"], email="owner@example.com")

    current_user = await auth_deps.get_current_user(authorization=f"Bearer {token}")

    assert current_user.cognito_sub == sub
    assert current_user.role == "owner"
    assert current_user.email == "owner@example.com"


@pytest.mark.asyncio
async def test_token_with_no_recognized_group_defaults_to_registered_user(rsa_keypair):
    private_key, _ = rsa_keypair
    token = _issue_token(private_key, groups=[])

    current_user = await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert current_user.role == "registered_user"


@pytest.mark.asyncio
async def test_token_with_multiple_groups_picks_a_recognized_one(rsa_keypair):
    private_key, _ = rsa_keypair
    token = _issue_token(private_key, groups=["some_other_group", "admin"])

    current_user = await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert current_user.role == "admin"


@pytest.mark.asyncio
async def test_missing_authorization_header_is_401():
    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_malformed_header_without_bearer_prefix_is_401(rsa_keypair):
    private_key, _ = rsa_keypair
    token = _issue_token(private_key)
    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=token)  # no "Bearer " prefix
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_signed_by_unknown_key_is_rejected(other_rsa_keypair):
    """Signature verification against the (fake) JWKS-resolved public key
    is the real security boundary here — a token signed by any other key
    must fail even though every other claim looks valid.
    """
    attacker_private_key, _ = other_rsa_keypair
    token = _issue_token(attacker_private_key, groups=["admin"])

    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_with_wrong_issuer_is_rejected(rsa_keypair):
    private_key, _ = rsa_keypair
    token = _issue_token(private_key, issuer="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_someoneelsepool")

    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_with_invalid_token_use_is_rejected(rsa_keypair):
    private_key, _ = rsa_keypair
    token = _issue_token(private_key, token_use="refresh")

    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_missing_sub_claim_is_rejected(rsa_keypair):
    private_key, _ = rsa_keypair
    claims = {"iss": _issuer(), "token_use": "id", "email": "x@example.com"}
    token = jwt.encode(claims, private_key, algorithm="RS256")

    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_app_client_id_mismatch_is_rejected_when_configured(
    monkeypatch: pytest.MonkeyPatch, rsa_keypair
):
    private_key, _ = rsa_keypair
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "expected-client-id")
    token = _issue_token(private_key, extra_claims={"client_id": "some-other-client-id"})

    with pytest.raises(AppError) as exc_info:
        await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_app_client_id_match_is_accepted_when_configured(
    monkeypatch: pytest.MonkeyPatch, rsa_keypair
):
    private_key, _ = rsa_keypair
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "expected-client-id")
    token = _issue_token(private_key, groups=["owner"], extra_claims={"client_id": "expected-client-id"})

    current_user = await auth_deps.get_current_user(authorization=f"Bearer {token}")
    assert current_user.role == "owner"

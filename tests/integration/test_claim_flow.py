"""Integration test: claim flow — submit, admin approve, admin reject.

DECISIONS.md "Claim flow: Google Business Profile match OR phone
verification, admin-reviewed, 2-business-day SLA" and
docs/API_CONTRACTS.md "Claim flow (/claim)". Runs against the real
FastAPI app + router + service layer + a real (SQLite, this sandbox) DB —
see tests/integration/conftest.py for why SQLite is fine here (no PostGIS
function is touched by any claim-flow code path).
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.owner_account import OwnerAccount
from factories import create_brand, create_location


@pytest.mark.asyncio
async def test_claim_submit_then_admin_approve(client, db_session, as_user):
    brand = await create_brand(db_session, is_claimed=False, owner_id=None)
    await create_location(db_session, brand_id=brand.id)
    await db_session.commit()

    claimant_sub = str(uuid.uuid4())
    claimant_email = f"{uuid.uuid4().hex[:8]}@example.com"
    as_user("registered_user", sub=claimant_sub, email=claimant_email)

    submit_resp = await client.post(
        "/claim",
        json={
            "brand_id": brand.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/test-listing",
        },
    )
    assert submit_resp.status_code == 201, submit_resp.text
    claim_body = submit_resp.json()
    assert claim_body["status"] == "pending_review"
    assert claim_body["brand_id"] == brand.id
    claim_id = claim_body["claim_id"]

    # Claim submission eagerly resolves/creates the claimant's owner_account
    # (see app/services/claim_service.py module docstring judgment call).
    owner_row = (
        await db_session.execute(select(OwnerAccount).where(OwnerAccount.cognito_sub == claimant_sub))
    ).scalar_one()
    assert owner_row.email == claimant_email

    # Admin approves.
    as_user("admin")
    approve_resp = await client.post(f"/claim/{claim_id}/approve", json={"reviewer_notes": "GBP matched"})
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"

    await db_session.refresh(brand)
    assert brand.owner_id == owner_row.id
    assert brand.is_claimed is True
    assert brand.claimed_at is not None


@pytest.mark.asyncio
async def test_claim_submit_then_admin_reject(client, db_session, as_user):
    brand = await create_brand(db_session, is_claimed=False, owner_id=None)
    await create_location(db_session, brand_id=brand.id)
    await db_session.commit()

    claimant_sub = str(uuid.uuid4())
    as_user("registered_user", sub=claimant_sub, email=f"{uuid.uuid4().hex[:8]}@example.com")

    submit_resp = await client.post(
        "/claim",
        json={
            "brand_id": brand.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/test-listing-2",
        },
    )
    assert submit_resp.status_code == 201
    claim_id = submit_resp.json()["claim_id"]

    as_user("admin")
    reject_resp = await client.post(
        f"/claim/{claim_id}/reject",
        json={"reviewer_notes": "Document did not match listing address."},
    )
    assert reject_resp.status_code == 200, reject_resp.text
    assert reject_resp.json()["status"] == "rejected"

    await db_session.refresh(brand)
    # Rejected claim must NOT attach ownership — brand stays unclaimed.
    assert brand.owner_id is None
    assert brand.is_claimed is False


@pytest.mark.asyncio
async def test_second_pending_claim_for_same_brand_is_conflict(client, db_session, as_user):
    """docs/API_CONTRACTS.md: "At most one pending_review claim can exist
    per brand at a time ... a second POST /claim for the same brand_id
    while one is already pending should return 409 Conflict."
    """
    brand = await create_brand(db_session, is_claimed=False, owner_id=None)
    await create_location(db_session, brand_id=brand.id)
    await db_session.commit()

    as_user("registered_user", sub=str(uuid.uuid4()))
    first = await client.post(
        "/claim",
        json={
            "brand_id": brand.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/first",
        },
    )
    assert first.status_code == 201

    # A different claimant tries to claim the same still-pending brand.
    as_user("registered_user", sub=str(uuid.uuid4()))
    second = await client.post(
        "/claim",
        json={
            "brand_id": brand.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/second",
        },
    )
    assert second.status_code == 409
    assert second.json()["code"] == "conflict" or "already pending" in second.json()["detail"]


@pytest.mark.asyncio
async def test_claimant_can_view_own_claim_but_not_someone_elses(client, db_session, as_user):
    brand_a = await create_brand(db_session, is_claimed=False, owner_id=None)
    brand_b = await create_brand(db_session, is_claimed=False, owner_id=None)
    await create_location(db_session, brand_id=brand_a.id)
    await create_location(db_session, brand_id=brand_b.id)
    await db_session.commit()

    claimant_a_sub = str(uuid.uuid4())
    as_user("registered_user", sub=claimant_a_sub)
    resp_a = await client.post(
        "/claim",
        json={
            "brand_id": brand_a.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/a",
        },
    )
    claim_a_id = resp_a.json()["claim_id"]

    claimant_b_sub = str(uuid.uuid4())
    as_user("registered_user", sub=claimant_b_sub)
    resp_b = await client.post(
        "/claim",
        json={
            "brand_id": brand_b.id,
            "proof_method": "google_business_profile",
            "google_business_profile_url": "https://business.google.com/b",
        },
    )
    assert resp_b.status_code == 201

    # Claimant B tries to view claimant A's claim -> 403.
    forbidden = await client.get(f"/claim/{claim_a_id}")
    assert forbidden.status_code == 403

    # Claimant A can view their own claim.
    as_user("registered_user", sub=claimant_a_sub)
    ok = await client.get(f"/claim/{claim_a_id}")
    assert ok.status_code == 200
    assert ok.json()["claim_id"] == claim_a_id


@pytest.mark.asyncio
async def test_phone_verification_requires_location_id_for_multi_location_brand(client, db_session, as_user):
    """docs/API_CONTRACTS.md: location_id is "required in practice when
    proof_method = phone_verification and the brand has more than one
    location."
    """
    brand = await create_brand(db_session, is_claimed=False, owner_id=None)
    await create_location(db_session, brand_id=brand.id, phone="+14695551111")
    await create_location(db_session, brand_id=brand.id, phone="+14695552222")
    await db_session.commit()

    as_user("registered_user", sub=str(uuid.uuid4()))
    resp = await client.post(
        "/claim",
        json={"brand_id": brand.id, "proof_method": "phone_verification"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "location_required"

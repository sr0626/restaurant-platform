"""claim_request — pending/resolved ownership claims on a restaurant_brand.

Backs DECISIONS.md "Claim flow: Google Business Profile match OR phone
verification, admin-reviewed, 2-business-day SLA" and implements the
`/claim` endpoints already specified in `docs/API_CONTRACTS.md` ("Claim
flow (`/claim`)") — that section explicitly flagged the backing table
as not yet built ("no `claim` entity is in the Architect's Phase 1
model list"); this is the follow-up that closes it.

Approval effect (already documented, unchanged here): on approve,
Backend Dev's service layer sets `restaurant_brand.owner_id =
<claimant>`, `is_claimed = true`, `claimed_at = now()` — those writes
land on `restaurant_brand`, not here. This table is the record of the
claim submission and its review outcome only.

Field-naming notes (kept consistent with the already-documented API
contract rather than re-deciding names — architect/CLAUDE.md "ALWAYS
keep docs current," and "never change a contract without flagging it"):
- `status` values are `pending_review` | `approved` | `rejected`,
  matching `docs/API_CONTRACTS.md` exactly (not the shorter `pending`
  used loosely in this task's own instructions).
- `reviewer_notes` matches the field name already used in both
  `GET /claim/{id}` and `POST /claim/{id}/reject` in
  `docs/API_CONTRACTS.md`, instead of a new `rejection_reason` column —
  it is documented as usable for notes on approval too, not reject-only.
- `supporting_document_key` stores the S3 object key. The API request/
  response field is named `supporting_document_url` in
  `docs/API_CONTRACTS.md`, but that section's own note already
  clarifies it is "an S3 key from a presigned upload" — this column
  name is accurate to what is actually stored; Backend Dev's Pydantic
  schema is what maps the external field name to this column.

JUDGMENT CALL (flagged for review): added `location_id` (nullable),
which is not in the currently-documented `/claim` request body. The
claim target is `restaurant_brand`, but the `phone_verification` proof
path calls "the phone number already on the public listing" per
DECISIONS.md — and phone lives on `restaurant_location`, not
`restaurant_brand`. For a multi-location brand there is no single
"the" phone number without picking a location. `location_id` records
which location's public phone was (or will be) used, so the schema
doesn't silently assume single-location brands. `docs/API_CONTRACTS.md`
is updated alongside this model to add it as an optional request
field. Confirm this before Backend Dev implements the
phone_verification path.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant_brand import RestaurantBrand
    from app.models.restaurant_location import RestaurantLocation


class ClaimRequest(TimestampMixin, Base):
    __tablename__ = "claim_request"
    __table_args__ = (
        # Makes the single admin queue ("oldest pending first, within
        # SLA") a cheap ordered scan instead of a filter + sort.
        Index(
            "ix_claim_request_status_submitted",
            "status",
            "submitted_at",
        ),
        # Partial unique: at most one *pending* claim per brand at a
        # time — avoids two competing claims resolving inconsistently
        # against the same unclaimed listing. Does not restrict how
        # many *resolved* (approved/rejected) claims a brand accumulates
        # over time. See JUDGMENT CALL note in the model docstring.
        Index(
            "uq_claim_request_pending_brand",
            "brand_id",
            unique=True,
            postgresql_where=text("status = 'pending_review'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    brand_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_brand.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which location's public phone number backs the phone_verification
    # path, for multi-location brands. See JUDGMENT CALL above.
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_location.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Cognito sub of the claimant — same pattern as
    # location_manager.user_id / user_follow.user_id (no local table for
    # every possible identity; Cognito is the source of truth).
    claimant_user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 'google_business_profile' | 'phone_verification' | 'document_upload'
    proof_method: Mapped[str] = mapped_column(String(32), nullable=False)

    google_business_profile_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    # S3 object key for the document-upload fallback proof path — see
    # field-naming note in the module docstring re: the API's
    # `supporting_document_url` name.
    supporting_document_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )

    # 'pending_review' | 'approved' | 'rejected' — see field-naming note.
    status: Mapped[str] = mapped_column(
        String(16), default="pending_review", nullable=False
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Admin Cognito sub who resolved the claim (approve or reject).
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped["RestaurantBrand"] = relationship()
    location: Mapped["RestaurantLocation | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ClaimRequest id={self.id} brand_id={self.brand_id} "
            f"status={self.status!r}>"
        )

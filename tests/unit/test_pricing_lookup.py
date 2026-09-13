"""Unit test: pricing lookup — DECISIONS.md "Pricing stored in
platform_pricing table with effective dates": "system reads most recent row
where effective_date <= today. No code deploy needed for price changes."

COVERAGE GAP (flagged, not a bug): there is no `pricing_service.py` and no
`/pricing`-shaped endpoint anywhere in `backend/app/` on this branch, and
`docs/API_CONTRACTS.md`'s Phase 1 endpoint families are exactly `/search`,
`/restaurants`, `/locations`, `/claim`, `/auth` — no pricing lookup is
actually wired up yet for this to unit-test beyond the bare model shape.
This is consistent with Phase 1 scope (billing/Stripe is Phase 2+ per root
CLAUDE.md "Current Phase") — nothing here indicates Backend Dev missed
something in scope, just that the "most recent effective_date <= today"
query logic doesn't exist as code yet. Reported as a coverage gap tied to
missing implementation, not something QA can test around or should invent
a service module for (tests/CLAUDE.md: "You do NOT write application
code").

What IS tested below: the `PlatformPricing` model itself constructs with
the documented shape/defaults (root CLAUDE.md "Billing model": "$100/mo or
$1,000/yr per location").
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models.platform_pricing import PlatformPricing


def test_platform_pricing_row_holds_documented_default_price_shape():
    today = date.today()
    row = PlatformPricing(
        monthly_price=Decimal("100.00"),
        yearly_price=Decimal("1000.00"),
        currency="USD",
        effective_date=today,
        created_by="admin-sub",
    )
    assert row.monthly_price == Decimal("100.00")
    assert row.yearly_price == Decimal("1000.00")
    assert row.currency == "USD"
    assert row.effective_date == today


def test_platform_pricing_supports_a_future_effective_dated_row():
    """DECISIONS.md: "Admin can set new price with future effective_date" —
    the model itself places no constraint on effective_date being <= today;
    that "most recent row <= today" selection is query logic that doesn't
    exist yet in Phase 1 (see module docstring coverage-gap note).
    """
    future = date.today() + timedelta(days=30)
    row = PlatformPricing(
        monthly_price=Decimal("120.00"),
        yearly_price=Decimal("1200.00"),
        currency="USD",
        effective_date=future,
    )
    assert row.effective_date > date.today()

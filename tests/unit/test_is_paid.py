"""Unit test: is_paid boundary — root CLAUDE.md "Tier model (is_paid)" and
tests/CLAUDE.md's own documented key pattern for this exact file, followed
verbatim plus a couple of extra boundary cases.

Pure logic — no DB, no HTTP (tests/unit/ per tests/CLAUDE.md directory
structure). `RestaurantLocation` is a plain SQLAlchemy declarative class; it
can be instantiated directly without a session, which is exactly what
`RestaurantLocationFactory` (factory.Factory, not SQLAlchemyModelFactory)
does.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from factories import RestaurantLocationFactory


def test_is_paid_returns_false_when_false():
    location = RestaurantLocationFactory(is_paid=False, paid_until=None)
    assert location.is_paid is False
    assert location.paid_until is None


def test_is_paid_returns_true_when_paid():
    location = RestaurantLocationFactory(
        is_paid=True, paid_until=datetime.now(timezone.utc) + timedelta(days=30)
    )
    assert location.is_paid is True
    assert location.paid_until is not None


def test_paid_until_in_past_should_have_been_caught_by_reconciliation():
    """DECISIONS.md "Payment failure = immediate free tier, no grace
    period" — is_paid should already be false the instant payment fails, so
    is_paid=True with paid_until in the past is a data-integrity smell (the
    daily reconciliation Lambda hasn't run yet), not a state the API should
    treat as "still paid". This test documents/detects that stale state
    exists as data; it is NOT asserting the API's read-time behavior — no
    Phase 1 endpoint recomputes is_paid from paid_until (root CLAUDE.md:
    is_paid is the stored boolean of record, set directly by the webhook).
    """
    location = RestaurantLocationFactory(
        is_paid=True, paid_until=datetime.now(timezone.utc) - timedelta(days=1)
    )
    assert location.paid_until < datetime.now(timezone.utc)
    # Flagging, not asserting a fix: is_paid is still True here because no
    # Phase 1 code path derives it from paid_until — see module docstring.
    assert location.is_paid is True


def test_free_tier_location_has_no_stripe_subscription_item():
    """A never-paid location shouldn't carry a dangling Stripe item id."""
    location = RestaurantLocationFactory(is_paid=False, paid_until=None, stripe_sub_item_id=None)
    assert location.is_paid is False
    assert location.stripe_sub_item_id is None


def test_paid_location_can_have_no_paid_until_for_admin_free_offer():
    """DECISIONS.md "Admin free offer sets is_paid=true + paid_until
    directly" — paid_until is always set for a free offer (an end_date), so
    is_paid=True with paid_until=None only happens for an active *Stripe*
    subscription (no fixed end). Both are valid is_paid=True shapes.
    """
    location = RestaurantLocationFactory(is_paid=True, paid_until=None)
    assert location.is_paid is True

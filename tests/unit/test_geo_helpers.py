"""Unit test: geo/hours helper math — no DB, no HTTP.

There is no standalone "distance between two lat/lngs" helper in the app
code to unit test in isolation: the actual 15-mile radius filter is a
PostGIS SQL expression (`ST_DWithin` / `ST_Distance` over a `Geography`
column in `app/services/search_service.py`) that only executes against a
real Postgres+PostGIS database — see
tests/integration/test_search_api.py for that (guarded — needs a real
Postgres+PostGIS, not available in this sandbox; see that file's docstring).

What *is* pure, DB-free logic worth covering here:
  - `app.services.hours_service._within` / `compute_is_open_now` — the
    open/closed display-status math (DECISIONS.md "Restaurant hours"),
    including the overnight (crosses-midnight) case.
  - `app.services.search_service._METERS_PER_MILE` and the DFW default
    fallback point — sanity-checked against an independent reference
    Haversine calculation (defined only in this test file, not app code)
    so the fixture coordinates used by the integration radius tests are
    known-good before they're ever run against real PostGIS.
"""
from __future__ import annotations

import math
from datetime import datetime, time, timezone

import pytest

from app.services import hours_service, search_service


class _FixedClock:
    """Stand-in for `datetime` inside hours_service — `.now(tz)` always
    returns the same instant regardless of the tz argument, so tests don't
    depend on wall-clock time or the machine's local timezone.
    """

    def __init__(self, fixed: datetime):
        self._fixed = fixed

    def now(self, tz=None):
        return self._fixed


# ---------------------------------------------------------------------------
# hours_service._within — pure function, no DB/clock involved at all.
# ---------------------------------------------------------------------------


def test_within_simple_daytime_window():
    assert hours_service._within(time(11, 0), time(22, 0), time(15, 0)) is True


def test_within_excludes_outside_daytime_window():
    assert hours_service._within(time(11, 0), time(22, 0), time(23, 0)) is False


def test_within_overnight_window_wraps_past_midnight():
    # Open 18:00, close 02:00 — 01:00 is "still open" (after open, before
    # midnight rollover close).
    assert hours_service._within(time(18, 0), time(2, 0), time(1, 0)) is True


def test_within_overnight_window_excludes_daytime_gap():
    assert hours_service._within(time(18, 0), time(2, 0), time(10, 0)) is False


# ---------------------------------------------------------------------------
# hours_service.compute_is_open_now — None-when-unknown, False-when-closed,
# time-window otherwise.
# ---------------------------------------------------------------------------


def test_compute_is_open_now_none_when_no_row_for_today():
    assert hours_service.compute_is_open_now(None, "America/Chicago") is None


def test_compute_is_open_now_none_when_is_closed_unknown():
    from app.models.restaurant_hours import RestaurantHours

    row = RestaurantHours(location_id=1, day_of_week=0, is_closed=None)
    assert hours_service.compute_is_open_now(row, "America/Chicago") is None


def test_compute_is_open_now_false_when_closed_all_day():
    from app.models.restaurant_hours import RestaurantHours

    row = RestaurantHours(location_id=1, day_of_week=0, is_closed=True)
    assert hours_service.compute_is_open_now(row, "America/Chicago") is False


def test_compute_is_open_now_true_within_window(monkeypatch: pytest.MonkeyPatch):
    from app.models.restaurant_hours import RestaurantHours

    fixed_now = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)  # any date; time-of-day is what matters
    monkeypatch.setattr(hours_service, "dt", _FixedClock(fixed_now))

    row = RestaurantHours(
        location_id=1, day_of_week=0, is_closed=False, open_time=time(11, 0), close_time=time(22, 0)
    )
    assert hours_service.compute_is_open_now(row, "America/Chicago") is True


def test_compute_is_open_now_false_outside_window(monkeypatch: pytest.MonkeyPatch):
    from app.models.restaurant_hours import RestaurantHours

    fixed_now = datetime(2026, 9, 14, 23, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(hours_service, "dt", _FixedClock(fixed_now))

    row = RestaurantHours(
        location_id=1, day_of_week=0, is_closed=False, open_time=time(11, 0), close_time=time(22, 0)
    )
    assert hours_service.compute_is_open_now(row, "America/Chicago") is False


def test_compute_is_open_now_true_for_overnight_window_past_midnight(monkeypatch: pytest.MonkeyPatch):
    from app.models.restaurant_hours import RestaurantHours

    fixed_now = datetime(2026, 9, 14, 1, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(hours_service, "dt", _FixedClock(fixed_now))

    row = RestaurantHours(
        location_id=1, day_of_week=0, is_closed=False, open_time=time(18, 0), close_time=time(2, 0)
    )
    assert hours_service.compute_is_open_now(row, "America/Chicago") is True


# ---------------------------------------------------------------------------
# search_service geo constants — cross-checked against an independent
# reference Haversine implementation (defined here only, for test sanity;
# NOT a claim that the app uses Haversine — it uses PostGIS's spheroid-based
# ST_Distance over a Geography column, which is more accurate and can only
# be exercised against real Postgres+PostGIS; see test_search_api.py).
# ---------------------------------------------------------------------------

_EARTH_RADIUS_MI = 3958.8


def _reference_haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_MI * math.asin(math.sqrt(a))


def test_meters_per_mile_constant_is_correct():
    assert math.isclose(search_service._METERS_PER_MILE, 1609.34, rel_tol=1e-6)


def test_default_fallback_point_is_dallas_tx():
    # DECISIONS.md "Default search radius: 15 miles" / search_service
    # module docstring judgment call: hardcoded Dallas, TX center fallback
    # when lat/lng are omitted. Sanity-checked against real Dallas, TX
    # coordinates (not the app's own literals re-typed blindly).
    dallas_lat, dallas_lng = 32.7767, -96.7970
    distance = _reference_haversine_miles(
        search_service._DEFAULT_LAT, search_service._DEFAULT_LNG, dallas_lat, dallas_lng
    )
    assert distance < 0.01


def test_reference_haversine_sanity_for_search_fixture_points():
    """Sanity-checks the "near" / "far" coordinate pairs that
    tests/integration/test_search_api.py's fixtures use, so a mistake in
    picking fixture lat/lngs is caught here (fast, no DB) rather than only
    surfacing as a confusing PostGIS integration-test failure.

    Irving, TX (32.8140, -96.9489) to a point ~0.07 deg north (~5 mi) should
    be comfortably inside a 15-mile radius; a point ~0.3 deg south (~21 mi)
    should be comfortably outside it.
    """
    irving_lat, irving_lng = 32.8140, -96.9489
    near_lat, near_lng = 32.8140 + 0.07, -96.9489
    far_lat, far_lng = 32.8140 - 0.30, -96.9489

    near_distance = _reference_haversine_miles(irving_lat, irving_lng, near_lat, near_lng)
    far_distance = _reference_haversine_miles(irving_lat, irving_lng, far_lat, far_lng)

    assert near_distance < 15
    assert far_distance > 15

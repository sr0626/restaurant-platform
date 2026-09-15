// Geo search behavior (tests/CLAUDE.md Phase 1 checklist: "Geo search
// returns correct results within 15 miles", "Geo search excludes results
// beyond radius"). The equivalent boundary math is already covered for
// real at the unit level (tests/unit/test_geo_helpers.py) and integration
// level (tests/integration/test_search_api.py, against a real Postgres +
// PostGIS test DB) — this file is specifically the browser-level version:
// typing a location into the real search UI and seeing real, geographically
// correct results.
//
// What's already covered at the e2e level without a backend — rendering,
// the cuisine-chip URL contract, and the graceful "can't load" empty state
// — lives in test_public_listing.spec.ts, not duplicated here.
import { test } from "@playwright/test";

test.fixme(
  "search returns restaurants within 15 miles of the entered location",
  async () => {
    // Needs: a live backend reachable at NEXT_PUBLIC_API_URL (local FastAPI
    // is enough — doesn't need to be the deployed Lambda) with seeded
    // restaurant_location rows at known coordinates, e.g. one 5 miles from
    // a test point (should appear) and one 20 miles away (should not) —
    // same fixture shape as tests/integration/test_search_api.py's
    // `test_search_returns_locations_within_15_miles`, just asserted
    // through the rendered SearchResults grid instead of the raw API
    // response.
  }
);

test.fixme("search excludes restaurants beyond the 15 mile radius", async () => {
  // Same blocker as above.
});

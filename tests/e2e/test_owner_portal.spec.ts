// Owner portal (tests/CLAUDE.md Phase 1 checklist: "Owner can edit basic
// listing info (free tier)", "Owner cannot access another owner's
// listing"). The unauthenticated-redirect half of this is real and covered
// in test_auth_redirects.spec.ts ("/portal/dashboard", "/portal/locations/1").
//
// Everything below needs a real signed-in owner session plus real seeded
// data (a brand/location owned by that test user, and a second owner's
// location to prove the boundary against) — see fixtures/auth.ts for what's
// missing and what unblocks it.
import { test } from "@playwright/test";
import { loginAs } from "./fixtures/auth";

test.fixme("owner sees their brands and locations on the dashboard", async ({ page }) => {
  // Needs: a real owner session with at least one seeded restaurant_brand +
  // restaurant_location, fetched via the real owner-scoped GET /restaurants.
  await loginAs(page, "owner");
  await page.goto("/portal/dashboard");
});

test.fixme(
  "owner can edit basic listing info for their own location (free tier)",
  async ({ page }) => {
    // Needs: real owner session + a real owned location id, exercising
    // LocationInfoForm.tsx against the real PUT /locations/{id}.
    await loginAs(page, "owner");
  }
);

test.fixme(
  "owner cannot access another owner's location editor (gets the generic not-found/no-access panel)",
  async ({ page }) => {
    // frontend/src/app/portal/locations/[id]/page.tsx already has the
    // right shape for this: a 403 from GET /locations/{id}/managers
    // renders the SAME NotFoundOrNoAccess panel as a real 404, so an
    // unauthorized owner can't distinguish "doesn't exist" from "exists,
    // not yours." Needs two real owners and a location owned by the
    // *other* one to actually exercise that server-side check — currently
    // nothing to log in as or a second owner's location id to hit.
    await loginAs(page, "owner");
  }
);

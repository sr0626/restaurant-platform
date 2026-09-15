// Manager portal / permission boundaries (Phase 2 checklist in
// tests/CLAUDE.md, but the frontend already has manager-facing UI in
// Phase 1 — components/portal/LocationManagerAssignment.tsx,
// app/portal/dashboard/page.tsx's manager branch — so it's tracked here
// now rather than left unwritten).
//
// All needs a real signed-in manager session plus real seeded
// owner/location/manager-assignment data — see fixtures/auth.ts.
import { test } from "@playwright/test";
import { loginAs } from "./fixtures/auth";

test.fixme(
  "manager dashboard explains there is no location list yet (known backend gap)",
  async ({ page }) => {
    // This one is PARTIALLY real today: app/portal/dashboard/page.tsx's
    // manager branch is unconditional UI (no API call — see its own
    // comment: "no other endpoint lets a manager discover which locations
    // they're assigned to"), so once loginAs() works this assertion needs
    // no seeded data at all. It's still gated behind a real session,
    // which is the actual blocker — not the assertion itself.
    await loginAs(page, "manager");
    await page.goto("/portal/dashboard");
  }
);

test.fixme("manager can edit an assigned location", async ({ page }) => {
  // Needs: real manager session + a real location_manager assignment row,
  // exercising the real PUT /locations/{id} manager path.
  await loginAs(page, "manager");
});

test.fixme(
  "manager gets a 403-equivalent (generic not-found/no-access panel) for an unassigned location",
  async ({ page }) => {
    // Needs: real manager session + a real location NOT assigned to them.
    await loginAs(page, "manager");
  }
);

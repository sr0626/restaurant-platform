// Claim flow (tests/CLAUDE.md Phase 1 checklist: "Claim flow: submit, admin
// approve, admin reject"). The unauthenticated-redirect half of this is
// real and covered in test_auth_redirects.spec.ts ("/claim?brand_id=1").
//
// Everything below needs a real signed-in session (submitting a claim as
// an authenticated user, then approving/rejecting it as an admin), which
// needs a real Cognito user pool — see fixtures/auth.ts for exactly what's
// missing and what unblocks it. Never faked here.
import { test } from "@playwright/test";
import { loginAs } from "./fixtures/auth";

test.fixme(
  "an authenticated user can submit a claim with proof, and it appears pending",
  async ({ page }) => {
    // Needs: a real signed-in session (any authenticated role, per
    // docs/API_CONTRACTS.md "POST /claim") and a real, unclaimed
    // restaurant_brand row to claim against a live backend.
    await loginAs(page, "registered_user");
    await page.goto("/restaurant/some-seeded-unclaimed-slug");
    // ClaimCTA.tsx links to /claim?brand_id={id}; ClaimForm.tsx has no
    // data-testid — once this is unblocked, drive it via its real
    // labeled fields/button text instead of inventing test ids here.
  }
);

test.fixme(
  "an admin can approve a pending claim, and the claimant gains portal access",
  async ({ page, context }) => {
    // Needs: a real admin session, plus a claim already in `pending` state
    // (created by the test above, or a seeded fixture) to act on via the
    // real `POST /claim/{id}/approve` endpoint.
    //
    // Also note (see app/admin/claims/page.tsx and
    // components/admin/ClaimReviewPanel.tsx's own flagged gap): there is
    // no list-all-pending-claims endpoint yet, only GET /claim/{id} — the
    // admin queue is lookup-by-id only. This test will need the claim id
    // up front, not a queue to browse, until that backend gap closes.
    const adminPage = await context.newPage();
    await loginAs(adminPage, "admin");
  }
);

test.fixme(
  "an admin can reject a pending claim, and the claimant is not granted access",
  async ({ page }) => {
    // Same blocker as above (real session + real pending claim).
    await loginAs(page, "admin");
  }
);

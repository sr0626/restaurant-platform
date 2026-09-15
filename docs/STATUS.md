# Project Status

Live snapshot — updated as work lands, not a historical log (see DECISIONS.md
for that). Phase 1 (MVP Core).

**Reality check: nothing is deployed to AWS yet.** Only real AWS resources
that exist: the `dev` account itself, the Terraform state S3 bucket +
DynamoDB lock table. `terraform apply` has never been run.

**⚠ Brand name risk — "Swaad" (still live in code) needs to change before commercial launch.**
Used throughout the frontend as a placeholder (it was never confirmed as a
final name). Real conflict found: "Swad" is a decades-old, actively
operating Indian grocery brand (spices/snacks), and "Indian Swaad" was a
registered US trademark specifically for restaurant/hotel services
(cancelled 2020, but shows direct precedent in this exact category). User
decision 2026-09-13: keep "Swaad" as the working placeholder for now (it's
centralized in a handful of files, easy to swap), but pick and clear a real
name before going live. Not a Phase 1 blocker, but flagged as urgent.
Working replacement name as of 2026-09-15: **Swarasa** (see DECISIONS.md
"Features & Product" for the full naming/logo history) — not yet applied
to any code. Logo direction ("Fork-E") is parked, not finalized; design
canvas: https://claude.ai/artifact/JAmSrrmd7k3NuDVMUKuT4U

## Open PRs
- None — all merged through #33 (see DECISIONS.md for what each did)

## Architect (schema + contracts)
- [x] 13 entities modeled, 2 migrations written (never run)
- [x] DATA_MODEL.md + API_CONTRACTS.md cover all Phase 1 endpoints
- [x] Location-manager contract, id/slug restaurant lookup contract — implemented + tests green
- [x] `GET /restaurants` (owner-scoped list) and `GET /cuisine-tags` (public)
      contracts written — implemented + tests green
- [x] Phase 1 completion plan produced (priority order + agent ownership for
      remaining pages: login, claim flow, admin claims queue, owner portal)

## Backend (FastAPI)
- [x] `/search`, `/restaurants` CRUD + owner-scoped list, `/restaurants/{id}/locations`
- [x] `/locations` CRUD + hours + photos sub-resource
- [x] `/locations/{id}/managers` (assign/list/remove)
- [x] `/claim` (submit/approve/reject), `/auth/me`
- [x] `/cuisine-tags` (public read list)
- [ ] Menu, deals, Stripe — Phase 2, not started (correctly)
- Container image built (Dockerfile), never pushed to ECR (no ECR repo exists yet)

## Frontend (Next.js)
- [x] Project scaffold, typed API client, auth helpers, route skeleton
- [x] Homepage built and merged: "Spice Market" direction, fully tokenized
      theme (Tailwind `brand.*` colors/fonts/radii/shadows — no hardcoded
      hex/fonts in components, so a future L&F change is a values-only edit)
- [x] Homepage wired to the real `/search` API client with graceful
      empty/error states — no fabricated restaurant data
- [x] Search results page and public restaurant detail page built (real
      results/pagination, hours, gallery, unclaimed-listing CTA)
- [x] Real Cognito login flow (email/password, in-memory token storage,
      server-verified session cookie — never localStorage)
- [x] Claim submission page + admin claims review queue (both Server
      Actions independently re-verify session/role server-side per call)
- [x] Owner dashboard + location editor (info, hours, photo gallery with
      free/paid limits, manager assignment with the 2-manager cap) —
      real presigned-S3 upload, 404/403 indistinguishable to unauthorized
      callers
- [x] Global error boundary (`app/error.tsx`) — found missing while manual
      testing; a data-fetch failure was falling through to Next.js's raw
      dev error screen instead of a graceful, branded state
- [x] Marketing copy reworded off repetitive "Indian" phrasing — new
      headline "Discover your taste," tagline "Discover Your Taste"
- [x] **`next build`/`next lint` fixed** — `next.config.ts` needed Next 15;
      converted to `next.config.mjs` (plain JS, works on the pinned Next
      14.2.18 — no version bump, per root `CLAUDE.md`'s settled Next 14
      stack decision). Verified with a real `next build` (success) and
      `next lint` (starts normally, no config-load error).
- `npm install` still unverified against the project's own npm registry
  (sandbox network issue) — verified once again against the public
  registry as a one-off; confirmed `@aws-amplify/auth@6.6.5` doesn't exist
  there (public jumps 6.5.2 → later 6.x series) — pin unchanged, needs a
  look separately. Also noted in passing: npm flags `next@14.2.18` itself
  for a known security advisory (nextjs.org/blog/security-update-2025-12-11)
  — separate from this fix, flagged for awareness.

## Infra (Terraform)
- [x] Modules written: aurora, ecr, lambda, cognito, s3, amplify, ses (deferred), eventbridge, iam, networking
- [ ] **Nothing applied — no Aurora, Lambda, Cognito, or ECR repo actually exist in AWS**
- State key convention set (`envs/dev/terraform.tfstate`) — needs `terraform init -migrate-state` before next apply

## DevOps (CI/CD)
- [x] `deploy-backend.yml` drafted
- [ ] Never run — no OIDC role deployed, no ECR repo, `DEV_DEPLOY_ROLE_ARN` secret not set

## QA / Tests
- [x] pytest: 109 passing, 3 skipped (need real Postgres), 0 failing
- [x] Playwright e2e: 17 passing, 12 explicitly skipped (`test.fixme` with
      reasons, not silently disabled) — covers public page rendering,
      mobile viewport (375px), unauthenticated-redirect, and the new error
      boundary. Skipped: anything needing real Cognito/live backend data
      (claim approval, owner/manager permission boundaries, geo search)
- Real gap found and flagged (not fixed — out of QA's scope): zero
  `data-testid` attributes anywhere in `frontend/src`; e2e suite falls back
  to role/text/aria selectors. Fast-follow, not a blocker.

## Process
- [x] Draft-PR-until-Architect-approved safeguard live (merge button
      disabled during review)
- [x] `docs/CMD_LOG.md` write pattern fixed — orchestrator-only now,
      feature branches no longer touch it (was causing a merge conflict on
      nearly every PR)
- Flagged, non-blocking gaps: no presigned-upload endpoint for claim
  documents; no list-all-pending-claims endpoint (admin queue is
  lookup-by-id only); no `data-testid` convention (above); manager has no
  way to discover assigned locations from the dashboard (owner-scoped
  `GET /restaurants` has no manager path); `cover_photo_url` has no photo
  id, so an already-set cover can't be explicitly deleted (only replaced)

## Blocking next steps
1. Adopt a `data-testid` convention (Frontend Dev) so the e2e suite's
   selectors are more resilient — not urgent, but the fast-follow to do
   before it's a pain to retrofit
2. Pick and clear a real brand name (see the ⚠ above) before commercial
   launch — not a Phase 1 dev blocker
3. `terraform apply` (human-run) — nothing goes live until this happens;
   Phase 1 is otherwise feature-complete and testable locally without it

# Project Status

Live snapshot — updated as work lands, not a historical log (see DECISIONS.md
for that). Phase 1 (MVP Core).

**Reality check: nothing is deployed to AWS yet.** Only real AWS resources
that exist: the `dev` account itself, the Terraform state S3 bucket +
DynamoDB lock table. `terraform apply` has never been run.

## Open PRs
- None — all merged through #14 (see DECISIONS.md for what each did)

## Architect (schema + contracts)
- [x] 13 entities modeled, 2 migrations written (never run)
- [x] DATA_MODEL.md + API_CONTRACTS.md cover all Phase 1 endpoints
- [x] Location-manager contract, id/slug restaurant lookup contract — implemented + tests green (92/3/0)

## Backend (FastAPI)
- [x] `/search`, `/restaurants` CRUD, `/restaurants/{id}/locations`
- [x] `/locations` CRUD + hours + photos sub-resource
- [x] `/locations/{id}/managers` (assign/list/remove)
- [x] `/claim` (submit/approve/reject), `/auth/me`
- [ ] Menu, deals, Stripe — Phase 2, not started (correctly)
- Container image built (Dockerfile), never pushed to ECR (no ECR repo exists yet)

## Frontend (Next.js)
- [x] Project scaffold, typed API client, auth helpers, route skeleton
- [x] Homepage built and merged: "Spice Market" direction, fully tokenized
      theme (Tailwind `brand.*` colors/fonts/radii/shadows — no hardcoded
      hex/fonts in components, so a future L&F change is a values-only edit)
- [x] Homepage wired to the real `/search` API client with graceful
      empty/error states — no fabricated restaurant data
- [ ] Search page and login page still unstyled placeholders
- [ ] **Known bug (repo-wide, pre-existing): `next build`/`next lint` don't
      run at all** — `next.config.ts` needs Next 15, pinned version is
      14.2.18. Fix suggested as a follow-up task, not yet started.
- `npm install` still unverified against the project's own npm registry
  (sandbox network issue) — verified once against the public registry as a
  one-off; `@aws-amplify/auth@6.6.5` pin doesn't exist there (needs a look)

## Infra (Terraform)
- [x] Modules written: aurora, ecr, lambda, cognito, s3, amplify, ses (deferred), eventbridge, iam, networking
- [ ] **Nothing applied — no Aurora, Lambda, Cognito, or ECR repo actually exist in AWS**
- State key convention set (`envs/dev/terraform.tfstate`) — needs `terraform init -migrate-state` before next apply

## DevOps (CI/CD)
- [x] `deploy-backend.yml` drafted
- [ ] Never run — no OIDC role deployed, no ECR repo, `DEV_DEPLOY_ROLE_ARN` secret not set

## QA / Tests
- [x] 94 passing, 3 skipped (need real Postgres), 0 failing — verified independently three times, incl. new slug-lookup coverage

## Blocking next steps
1. Fix the `next.config.ts`/Next 14 incompatibility so the frontend can
   actually build (queued as a follow-up task)
2. Style the remaining pages (search, login)
3. `terraform apply` (human-run) — nothing goes live until this happens

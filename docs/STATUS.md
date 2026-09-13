# Project Status

Live snapshot — updated as work lands, not a historical log (see DECISIONS.md
for that). Phase 1 (MVP Core).

**Reality check: nothing is deployed to AWS yet.** Only real AWS resources
that exist: the `dev` account itself, the Terraform state S3 bucket +
DynamoDB lock table. `terraform apply` has never been run.

## Open PRs
- #7 backend API + location-manager routes + tests — Architect approved, one more commit incoming (id/slug fix)
- #8 frontend scaffold — Architect approved
- #9 infra service_name + state key — Architect approved
- #10 infra Cognito ListUsers grant — Architect approved
- #11 Architect fix-loop rule (docs) — ready, self-authored
- #12 restaurants id/slug contract fix (docs) — ready, self-authored

## Architect (schema + contracts)
- [x] 13 entities modeled, 2 migrations written (never run)
- [x] DATA_MODEL.md + API_CONTRACTS.md cover all Phase 1 endpoints
- [x] Location-manager contract, id/slug restaurant lookup contract

## Backend (FastAPI)
- [x] `/search`, `/restaurants` CRUD, `/restaurants/{id}/locations`
- [x] `/locations` CRUD + hours + photos sub-resource
- [x] `/locations/{id}/managers` (assign/list/remove)
- [x] `/claim` (submit/approve/reject), `/auth/me`
- [ ] Menu, deals, Stripe — Phase 2, not started (correctly)
- Container image built (Dockerfile), never pushed to ECR (no ECR repo exists yet)

## Frontend (Next.js)
- [x] Project scaffold, typed API client, auth helpers, route skeleton
- [ ] **All pages are unstyled placeholders — zero visual design**
- Blocked on: homepage/search color-scheme pick (5-option canvas awaiting review)
- `npm install` never run — versions unverified

## Infra (Terraform)
- [x] Modules written: aurora, ecr, lambda, cognito, s3, amplify, ses (deferred), eventbridge, iam, networking
- [ ] **Nothing applied — no Aurora, Lambda, Cognito, or ECR repo actually exist in AWS**
- State key convention set (`envs/dev/terraform.tfstate`) — needs `terraform init -migrate-state` before next apply

## DevOps (CI/CD)
- [x] `deploy-backend.yml` drafted
- [ ] Never run — no OIDC role deployed, no ECR repo, `DEV_DEPLOY_ROLE_ARN` secret not set

## QA / Tests
- [x] 92 passing, 3 skipped (need real Postgres), 0 failing — verified independently twice

## Blocking next steps
1. Merge the open PRs
2. Pick a homepage design direction
3. `terraform apply` (human-run) — nothing goes live until this happens

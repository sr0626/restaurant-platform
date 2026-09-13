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
- [x] Homepage direction picked: "Spice Market" (see DECISIONS.md) — tokenized
      theme (Tailwind + CSS vars), homepage build in progress
- [ ] Search page and rest of the app still unstyled placeholders
- `npm install` never run — versions unverified

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
1. Land the Spice Market homepage build (Frontend Dev in progress)
2. `terraform apply` (human-run) — nothing goes live until this happens

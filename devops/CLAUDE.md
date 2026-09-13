# DevOps Agent

> First read the root `/CLAUDE.md` — it contains shared context, stack, and
> universal guardrails that apply to this agent too.

## Role
You are the DevOps agent for the Restaurant Discovery Platform. Added
2026-09-12 — see `docs/DECISIONS.md` "Agent Architecture." You own CI/CD:
building and pushing container images, deploying them, and (once more
accounts exist) promoting a built image across environments. You do NOT own
the Terraform resource definitions themselves — that's Infra. You do NOT own
application code — that's Backend Dev / Frontend Dev / Architect.

**Boundary with Infra:** Infra defines the ECR repository, the Lambda
function resource, and IAM roles as Terraform resources (`/infra/modules/ecr`,
`/infra/modules/lambda`). You define and run the pipeline that builds an
image, pushes it to that repository, and points the Lambda function at the
new image (`aws lambda update-function-code` or an equivalent Terraform-
variable-driven update) — the code-shipping motion, not the resource shape.

## Directory Structure
```
/devops
  CLAUDE.md
  /.github-workflows-templates   ← drafts; actual workflows live at repo root
                                    /.github/workflows/ once approved
  /scripts
    build-and-push.sh            ← docker build + ecr push for one service
    deploy-lambda.sh             ← point a Lambda function at a new image
```
(`.github/workflows/*.yml` itself lives at the repo root, per GitHub's
requirement — this agent authors those files even though they're not under
`/devops`, same pattern as Architect owning files under `/backend`.)

## Stack
- GitHub Actions (already decided as the CI/CD tool — see root `CLAUDE.md`)
- Docker (build the Lambda container image from `/backend/Dockerfile`)
- AWS ECR (image registry — Infra-defined repo, you push to it)
- AWS CLI / boto3 for the deploy step (`update-function-code`)
- GitHub OIDC → AWS IAM role assumption (no long-lived AWS keys in GitHub secrets)

## Key Patterns

### Build-and-push (dev account, Phase 1 — single account, no promotion yet)
```yaml
# .github/workflows/deploy-backend.yml (draft — human reviews before it's live)
on:
  push:
    branches: [main]
    paths: ["backend/**"]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # required for OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.DEV_DEPLOY_ROLE_ARN }}   # OIDC, no static keys
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -t $ECR_REPO:${{ github.sha }} backend/
          docker push $ECR_REPO:${{ github.sha }}
      - run: |
          aws lambda update-function-code \
            --function-name restaurant-platform-api-dev \
            --image-uri $ECR_REPO:${{ github.sha }}
```
Note: this workflow runs unattended in CI once the human has reviewed and
merged it — the "no automatic AWS commands" rule in root `CLAUDE.md` governs
*this Claude Code session* acting on the human's behalf, not a CI pipeline the
human has already reviewed and approved into existence. Getting a new
workflow file merged still goes through normal PR review.

### Promotion across environments (Phase 2+, once `test`/`prod` exist)
Not built yet — only `dev` exists (see root `CLAUDE.md` "Environments"). When
`test`/`prod` accounts are added: promotion means re-tagging/re-pulling the
**same image digest** into the next account's ECR (rebuilding from source in
each environment defeats the point of "tested this exact artifact"), then
running the same `update-function-code` deploy step there. Design this when
the second account actually exists, not speculatively now.

**Migration-before-image, per environment (added 2026-09-12 — see
DECISIONS.md "Terraform environment promotion").** Once this pipeline
promotes across more than one environment, each environment's promotion step
is two ordered sub-steps, never reversed: (1) a human runs Alembic `upgrade`
against that environment's Aurora database using the migration files already
reviewed on `main`; (2) only once that succeeds, the deploy step points that
environment's Lambda at the new image digest. If the migration fails, the
image does not move forward into that environment. This is why Architect's
migrations default to additive/expand-contract (see DECISIONS.md) — it's what
makes the brief window between step (1) and (2) safe for whichever image
happens to be serving traffic at that moment.

**Plan-all script, once more than one environment exists (light automation,
never an apply).** "A human runs `terraform apply` against each environment
in sequence" is fine at one environment; it gets error-prone and slow once
`test`/`prod` exist and the module count under `/infra/modules` has grown.
Build `infra/scripts/plan-all.sh` (or an equivalent DevOps/Infra-shared
script) that loops over each environment's state key + var-file + profile,
runs `terraform plan` for each, and prints/saves the three diffs together for
human review in one pass. It never calls `apply` — that stays human-run,
per-environment, exactly as today. This is a convenience layer over an
unchanged guardrail, not a loosening of it.

**Rollback playbook (added 2026-09-12 — see DECISIONS.md "Terraform rollback
playbook").** App-code rollback is symmetric and cheap: re-run the deploy
step with the previous image digest. Terraform rollback is not — reapplying
an older commit diffs against *current* state, it doesn't restore a prior
state snapshot, so a "rollback" apply can itself be destructive (e.g. drop a
column/table that current data now depends on). The guardrails:
- Roll forward, don't roll back: fix a bad apply with a new reviewed commit
  that repairs current state, not by reapplying old history.
- Every stateful resource (Aurora, the S3 media bucket, anything not
  trivially recreated) carries `lifecycle { prevent_destroy = true }` from
  the point it's created — a plan that would destroy/replace one of these
  fails instead of quietly succeeding.
- Any plan showing a destroy/replace on a `prevent_destroy`-guarded resource
  is a hard stop — flag it to the human explicitly, don't let it ride along
  as one line in a larger diff.

**Hotfix path once `test`/`prod` exist (added 2026-09-12 — see DECISIONS.md
"Hotfix path").** A critical bug found in `test` or `prod` still goes through
the standard feature-branch → PR → Architect review → human merge flow — no
long-lived branch, no skipped review. What changes for a genuinely urgent
fix: label the PR `hotfix` so Architect's review can focus tightly
(schema/security/scope, not full design) rather than skip; the human may
promote straight to `prod` ahead of `test` if `test` doesn't reproduce the
issue and explicitly approves the skip; but the same commit must be
backfilled into `test` in the very next promotion pass, and the out-of-order
promotion gets a `docs/CMD_LOG.md` note — environments never silently diverge
on which commit their state reflects.

**Multi-service scaling (added 2026-09-12 — see DECISIONS.md "Multi-service
scaling").** A second Lambda function/service later is a copy of the existing
pattern, not a redesign, once `infra/modules/ecr` and `infra/modules/lambda`
carry a `service_name` variable (Infra's addition, defaulting to `"api"` so
today's single-service call site is unaffected): a second `module "ecr"` /
`module "lambda"` block with `service_name = "notifications"` (or whatever
the service is), a second CI workflow (or a matrix job in the existing one)
with its own `paths:` filter, and its own OIDC role scoped to that one repo
and that one function — IAM scoping stays "one repo, one function" per
service, never widened to cover both.

## Phase 1 Scope — What to Build Now
- `backend/Dockerfile` (coordinate with Backend Dev — you consume it, you
  don't own its contents)
- `.github/workflows/deploy-backend.yml` — build, push to `dev` ECR, deploy to
  `dev` Lambda on merge to `main`
- The IAM OIDC trust role Infra provisions for you (you specify what
  permissions the pipeline needs; Infra writes the Terraform for the role)

## Phase 1 — Do NOT Build Yet
- Cross-account promotion pipeline (no `test`/`prod` account exists yet)
- Blue/green or canary deploys (unnecessary complexity at Phase 1 traffic)
- Automated rollback (start manual — re-run the workflow with the previous
  commit SHA if a deploy is bad)

## Guardrails (DevOps-Specific)

### NEVER
- NEVER put static AWS access keys in GitHub secrets — OIDC role assumption only
- NEVER give the pipeline's IAM role permissions beyond what it needs
  (ECR push/pull to its own repo, `lambda:UpdateFunctionCode` on its own
  function — not account-wide admin)
- NEVER have CI run `terraform apply` — infrastructure changes are still
  human-applied; CI only ships application code into resources that already exist
- NEVER build and deploy without the human having reviewed the workflow file
  itself first (this is a one-time review per workflow, not per-run)

### ALWAYS
- ALWAYS create a feature branch before making changes and open a PR when
  done — never commit/push to `main`, never merge your own PR (see root
  `CLAUDE.md` "Git Workflow"). Applies to workflow files and scripts the same
  as application code.
- ALWAYS tag images immutably (commit SHA or digest, never `:latest`) so a
  deploy is reproducible and promotable
- ALWAYS scan images on push (ECR `scan_on_push`, Infra-configured) and stop
  the pipeline on critical findings
- ALWAYS make the deploy step idempotent — re-running the same workflow twice
  should be safe

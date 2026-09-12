# Restaurant Discovery Platform — Root Context

## Project
Indian Restaurant Discovery & Deals Platform.
A location-based directory for Indian restaurants with regional cuisine filters,
owner-managed menus, time-limited deals, and subscription billing.

## Current Phase
**PHASE 1 — MVP Core (Weeks 1–3)**
Build the verified DFW restaurant directory with geo search and basic owner portal.
Do not build Phase 2 features (payments, deals, analytics) during Phase 1.

## Stack (all AWS, no external vendors)
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Mangum (Lambda adapter)
- **Backend packaging:** container image via ECR, run on Lambda (`package_type =
  "Image"`) — not zip. Changed 2026-09-12 for cross-account promotion; see
  DECISIONS.md "Containerization". Still scale-to-zero, still pay-per-invocation.
- **Database:** Aurora PostgreSQL Serverless v2 + PostGIS extension
- **Frontend:** Next.js 14 (TypeScript), Tailwind CSS, AWS Amplify hosting
- **Auth:** AWS Cognito (user pools: owner, manager, admin, registered_user)
- **Media:** S3 + CloudFront (presigned URLs for upload, never through Lambda)
- **Email:** AWS SES (deferred — Phase 2+; Cognito uses built-in mailer for Phase 1)
- **Payments:** Stripe (Phase 2+)
- **Scheduling:** Single EventBridge cron Lambda (deal expiry)
- **IaC:** Terraform 1.7+
- **CI/CD:** GitHub Actions (OIDC → AWS role assumption, no static keys — owned
  by the DevOps agent)

## Environments (added 2026-09-12 — see DECISIONS.md "AWS account structure")
- **AWS Organizations, one member account per environment**, under the user's
  existing management/payer account (consolidated billing, no new payment
  method per account).
- **Only `dev` exists right now.** `test` and `prod` will be added later, same
  pattern, when there's something worth staging or launching. Don't design or
  provision cross-account plumbing (promotion pipelines, cross-account IAM
  trust) before the second account actually exists.
- Every agent targets the environment named in `var.env` (Infra) or the active
  AWS CLI profile (DevOps) — never hardcode `dev`, `test`, or `prod` where a
  variable should be used instead, so adding the next account later is a
  config change, not a code change.
- Account creation itself is manual (human does it via AWS Organizations
  console or CLI) — no agent runs `organizations:CreateAccount`.

## Repository Structure
```
/restaurant-app
  CLAUDE.md               ← this file (root, all agents read)
  orchestrator.py          ← task decomposition + dispatch (active from Phase 1)
  /architect               ← DB schema, migrations, API/data contracts
    CLAUDE.md             ← Architect agent instructions
  /backend                ← FastAPI app, Lambda handlers, Dockerfile
    CLAUDE.md             ← Backend Dev agent instructions
  /devops                 ← CI/CD pipelines, container build/push/deploy
    CLAUDE.md             ← DevOps agent instructions
  /frontend               ← Next.js app
    CLAUDE.md             ← Frontend Dev agent instructions
  /infra                  ← Terraform modules
    CLAUDE.md             ← Infra agent instructions
  /tests                  ← pytest + Playwright
    CLAUDE.md             ← QA agent instructions
  /docs
    AGENT_DESIGN.md       ← agent architecture document
    BRD_v36_Restaurant_Platform.docx          ← business requirements
```

## Key Domain Concepts (read before writing any code)

### Ownership hierarchy
```
owner_account (1) → restaurant_brand (N) → restaurant_location (N) → location_manager (N)
```
- One owner can have multiple brands (same or different names)
- One brand can have multiple locations
- Each location has its own paid/free status
- A manager can manage multiple locations (assigned by owner)

### Tier model (is_paid)
Tier is NOT a stored enum. It is a boolean on `restaurant_location`:
```sql
is_paid      BOOLEAN DEFAULT false
paid_until   TIMESTAMP              -- NULL when free
```
- Stripe webhook sets `is_paid=true` + `paid_until` on payment success
- Stripe webhook sets `is_paid=false` + `paid_until=NULL` on payment failure — IMMEDIATELY
- Admin can set `is_paid=true` + `paid_until=offer_end_date` for free offers
- ALWAYS check `is_paid` before returning any paid-tier content

### Billing model
- Stripe: one subscription per owner, one Subscription Item per paid location
- One consolidated invoice per month
- $100/mo or $1,000/yr per location (stored in `platform_pricing` table — not hardcoded)
- Managers can initiate upgrades; only owners can downgrade or cancel

### Paid content behaviour
- Downgrade: paid content hides immediately (is_paid=false), NOT deleted
- Re-subscribe: paid content reappears immediately (is_paid=true)
- is_paid=false locations: dish photos beyond the free gallery limit, deals,
  custom page, full analytics, and promoted placement are NOT returned by API.
  Full menu with prices IS returned regardless of is_paid — it's a free feature
  (see BRD section 3.3, DECISIONS.md "Full menu with prices moved to free tier")
- Paid tier also caps `location_manager` assignments at 2 per location

### Permission model
Every write request must be validated server-side:
- Owner: full access to all their brands/locations
- Manager: only locations explicitly assigned (check location_manager table on every write)
- Admin: full platform access
- Registered user: read-only + follow + deals
- Public: read-only (no deals)

## Coding Conventions

### Python
- Type hints on all function signatures
- Pydantic v2 for request/response schemas
- SQLAlchemy 2.x async sessions
- All endpoints in `/backend/app/routers/`
- All DB models in `/backend/app/models/`
- All business logic in `/backend/app/services/`
- File naming: `snake_case.py`

### TypeScript / Next.js
- Strict mode enabled
- Components in `/frontend/src/components/`
- Pages in `/frontend/src/app/` (App Router)
- API calls in `/frontend/src/lib/api/`
- No `any` types

### Terraform
- One module per AWS service in `/infra/modules/`
- Variables in `variables.tf`, outputs in `outputs.tf`
- No hardcoded region — use `var.aws_region`
- Tag all resources: `project`, `phase`, `env`

### Git
- Branch per feature: `feature/phase1-search-api`
- Commit messages: `feat:`, `fix:`, `test:`, `infra:`, `docs:`
- No commits directly to `main`

### Git Workflow (standing rule, added 2026-09-12 — no exceptions)
Every agent, every task, follows this flow — codified per-agent in each
`CLAUDE.md`'s guardrails too:
1. **Create a feature branch before making any change.** Prefix matches the
   work: `feature/`, `infra/`, `fix/`, `docs/` (see naming above). Never
   write directly on `main`.
2. Commit to that branch as work progresses (commit freely — no permission
   needed for a local commit on a feature branch, same as always).
3. **Pushing the branch and opening the PR both require the same per-action
   explicit permission as any `git push`** (see "NEVER — Session Control"
   below) — this didn't change, it now also covers feature branches, not
   just `main`.
4. Open the PR against `main` (`gh pr create`) once pushed.
5. **The Architect agent reviews every PR — schema, backend, frontend,
   infra, devops, tests alike — and adds review comments.** Architect
   doesn't need infra/frontend expertise to catch scope creep, missing
   tests, or a mismatch with `docs/DECISIONS.md`; that's the point of a
   single consistent review gate. Exception: a PR Architect itself opened
   skips Architect self-review and goes straight to human review.
6. **The human manually approves and merges. No agent ever merges a PR —
   its own or anyone else's — under any circumstance.**

## Universal Guardrails (apply to ALL agents)

### NEVER — Cost
- NEVER provision always-on compute above $50/mo without approval
- NEVER create a NAT Gateway
- NEVER enable Aurora multi-AZ without approval
- NEVER remove Aurora `min_capacity = 0` (must scale to zero when idle)

### NEVER — Security
- NEVER hardcode secrets, keys, tokens, or passwords in any file
- NEVER create IAM policy with `*` on Action or Resource
- NEVER make an S3 bucket public (except designated CloudFront distribution bucket)
- NEVER commit `.env` or `terraform.tfvars` with real values (use `.gitignore`)
- NEVER expose internal stack details in API error responses (use generic messages)

### ALWAYS — AWS Best Practices (all agents, standing rule, added 2026-09-12)
Applies to every agent, not just Infra/DevOps — Architect's schema/access
patterns, Backend Dev's SDK calls, and QA's test fixtures all touch AWS
indirectly and must follow the same principles:
- ALWAYS design and code for least privilege — request/use only the specific
  IAM actions and resource scopes a task actually needs, never a broader
  grant "to be safe." If a task seems to need broader access than it has,
  flag it to Infra rather than working around it.
- ALWAYS assume data is encrypted at rest and in transit (Aurora, S3, Secrets
  Manager already are) — never design a path that bypasses that (e.g. an
  unencrypted export, a public read path around CloudFront/OAC).
  Infra/DevOps-specific detail lives in their own `CLAUDE.md` (IAM
  least-privilege rules, ECR scan-on-push, OIDC over static keys, etc.) —
  this is the version every other agent applies in their own domain.

### NEVER — Scope
- NEVER build features outside current phase scope (see Current Phase above)
- NEVER run `terraform apply` — generate plan only
- NEVER run Alembic migrations — generate migration files only
- NEVER delete or truncate any DB table or S3 bucket
- NEVER modify files outside your designated directory without explicit instruction

### NEVER — Session Control (no exceptions, standing rule)
- NEVER run `git push` on your own authority, even if a previous push in this
  session was approved. Every push needs its own explicit go-ahead from the
  human — either they type the command themselves, or they say yes to this
  specific push. Approving one push does not carry over to the next. Applies
  to feature-branch pushes and `gh pr create` exactly the same as `main`.
- NEVER work directly on `main` — create a feature branch first, every task,
  no exceptions (see "Git Workflow" above).
- NEVER merge a pull request — yours or another agent's — for any reason.
  Only the human merges. This is absolute, not just a default.
- NEVER run any AWS CLI or SDK command that touches real AWS (`aws ...`,
  `boto3` calls, `terraform apply`/`import`/`destroy`, etc.) without explicit
  permission for that exact command, every single time. This includes
  read-only-seeming commands (`aws s3 ls`, `aws sts get-caller-identity`) —
  ask first regardless. No standing approval accumulates across a session.
- NEVER let a `git push` or an AWS CLI/SDK command go unlogged — see the
  "ALWAYS — Command Log" rule below, no exceptions.

### ALWAYS — Command Log (no exceptions, standing rule)
- ALWAYS record every `git push`, every AWS CLI/SDK command, and every
  `terraform plan`/`apply` in `docs/CMD_LOG.md` — grouped by date, in
  execution order, tagged `# user` or `# claude`. Keep it to just the
  command list, no description or explanation.

### ALWAYS — Quality
- ALWAYS write a test alongside every new endpoint, component, or Lambda
- ALWAYS use Alembic for schema changes — no raw DDL statements
- ALWAYS write an `audit_log` entry for every write on: restaurant_brand,
  restaurant_location, menu_item, deal, owner_account, location_manager
- ALWAYS check `is_paid` before returning any paid-tier content
- ALWAYS validate manager assignment server-side on every write (never trust JWT alone)

### ALWAYS — Documentation (no exceptions, standing rule)
- ALWAYS bump the version and add a Version History row (in the BRD document
  itself) whenever BRD content changes — no silent edits. See DECISIONS.md
  "Process & Documentation" for the exact steps (bump version, log the row,
  rename the file, update the 3 references to it).
- ALWAYS keep the previous 2 versioned BRD `.docx` files on disk (n-2
  retention: current + 2 prior) — never delete an old version's file in the
  same change that creates a new one. Only clean up the oldest once a 4th
  version file would otherwise exist.

## Decision-Making Autonomy (standing rule, added 2026-09-12)
Architect and the orchestrator make the call on ambiguous design/schema/
process questions themselves — don't stop mid-task to ask about something
you can reason through (field naming, a cascade behavior, how to phase a
plan, which of several reasonable approaches to take). Decide, implement,
and **clearly report what you decided and why** so the human can question,
override, or approve it afterward — this is a "propose the plan, then
answer questions" model, not "ask before every decision." The prior Architect
tasks this session already did this well (flagged judgment calls in the
report rather than blocking on them) — keep doing that, and apply the same
posture to orchestrator-level planning (subtask breakdowns, sequencing,
which agent does what).

This does NOT relax anything in "Ask Human When" below, or any of the
"no exceptions" standing rules elsewhere in this file (git push, AWS
commands, PR merges, feature-branch workflow) — those still require
explicit per-action permission or a stop-and-ask, always. This rule is about
substantive design/process judgment calls, not about the hard gates.

## Ask Human When
Stop and ask before proceeding if:
- A task requires touching more than one agent's directory
- A decision would cost more than $50/mo when live
- The task is irreversible (deleting data, publishing to production)
- The requirement is ambiguous between two valid interpretations with
  meaningfully different consequences (not just "which of these two
  reasonable field names" — see Decision-Making Autonomy above)
- A security decision has no clear right answer

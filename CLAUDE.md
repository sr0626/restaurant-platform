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
- **Database:** Aurora PostgreSQL Serverless v2 + PostGIS extension
- **Frontend:** Next.js 14 (TypeScript), Tailwind CSS, AWS Amplify hosting
- **Auth:** AWS Cognito (user pools: owner, manager, admin, registered_user)
- **Media:** S3 + CloudFront (presigned URLs for upload, never through Lambda)
- **Email:** AWS SES
- **Payments:** Stripe (Phase 2+)
- **Scheduling:** Single EventBridge cron Lambda (deal expiry)
- **IaC:** Terraform 1.7+
- **CI/CD:** GitHub Actions

## Repository Structure
```
/restaurant-app
  CLAUDE.md               ← this file (root, all agents read)
  /backend                ← FastAPI app, Lambda handlers, DB models
    CLAUDE.md             ← Backend Dev agent instructions
  /frontend               ← Next.js app
    CLAUDE.md             ← Frontend Dev agent instructions
  /infra                  ← Terraform modules
    CLAUDE.md             ← Infra agent instructions
  /tests                  ← pytest + Playwright
    CLAUDE.md             ← QA agent instructions
  /docs
    AGENT_DESIGN.md       ← agent architecture document
    BRD_v35.docx          ← business requirements
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
- is_paid=false locations: menus, deals, custom page not returned by API

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

### NEVER — Scope
- NEVER build features outside current phase scope (see Current Phase above)
- NEVER run `terraform apply` — generate plan only
- NEVER run Alembic migrations — generate migration files only
- NEVER delete or truncate any DB table or S3 bucket
- NEVER modify files outside your designated directory without explicit instruction

### ALWAYS — Quality
- ALWAYS write a test alongside every new endpoint, component, or Lambda
- ALWAYS use Alembic for schema changes — no raw DDL statements
- ALWAYS write an `audit_log` entry for every write on: restaurant_brand,
  restaurant_location, menu_item, deal, owner_account, location_manager
- ALWAYS check `is_paid` before returning any paid-tier content
- ALWAYS validate manager assignment server-side on every write (never trust JWT alone)

## Ask Human When
Stop and ask before proceeding if:
- A task requires touching more than one agent's directory
- A decision would cost more than $50/mo when live
- The task is irreversible (deleting data, publishing to production)
- The requirement is ambiguous between two valid interpretations
- A security decision has no clear right answer

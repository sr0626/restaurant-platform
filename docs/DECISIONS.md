# Architecture Decision Log

Every significant technical or product decision made for this project.
Read this before asking "why did we do X?" — the answer is probably here.
When a new decision is made, add it to the top of the relevant section.

Format: **Decision** | Date | Reasoning | Alternatives Rejected

---

## Process & Documentation

**Architect must post an explicit confirmation/approval verdict on every PR before it's surfaced to the human — standing rule, tightened from "adds comments"**
2026-09-12 | User decision. The prior rule only required Architect to leave
review comments; this raises the bar to an unambiguous go/no-go verdict
("Architect approval: ready to merge" / "Architect: do not merge until X"),
and the PR must not be presented to the human as "ready for your review"
until that verdict exists. Self-review exception unchanged and explicitly
reconfirmed by the user: a PR Architect itself opened skips straight to
human review, no one reviews the reviewer. Same exception extended to
BRD-only PRs (business document, not code — see "Every BRD update..."
entry below). Architect posts the verdict as the closing line of a plain
PR comment, not via `gh pr review --approve` — a native GitHub approval
would be attributed to the same account as the human's own reviews (no
separate bot identity exists), blurring who actually decided what.
*Rejected: using `gh pr review --approve`/`--request-changes` for the verdict
(identity confusion, same GitHub account as the human), requiring Architect
confirmation on its own PRs too (no reviewer for the reviewer — user
explicitly confirmed keeping this exception when asked)*

**Architect and the orchestrator decide judgment calls themselves and report the plan — standing rule**
2026-09-12 | User decision: don't stop mid-task to ask about ambiguous
design/schema/process questions with a reasonable answer (field naming, a
cascade rule, how to sequence a plan) — decide, implement, and clearly
report the decision and reasoning so the human can question, override, or
approve it afterward. This is "propose the plan, then take questions," not
"ask before every decision." Explicitly does NOT relax any "no exceptions"
standing rule (git push, AWS commands, PR merges, feature-branch workflow)
or the existing "Ask Human When" triggers (cross-directory work, >$50/mo,
irreversible actions, genuinely ambiguous requirements, no-clear-answer
security calls) — those remain hard stops. Codified in root `CLAUDE.md`
("Decision-Making Autonomy") and `architect/CLAUDE.md`.
*Rejected: keeping the prior ask-first posture (the two Architect tasks this
session already showed that deciding-and-flagging produces better results
than blocking on every judgment call)*

**Every agent works on a feature branch and opens a PR — no direct commits/pushes to `main`, Architect reviews, human merges — standing rule, no exceptions**
2026-09-12 | User decision. Formalizes and enforces what README.md's Git
Conventions already said aspirationally ("No direct commits to main. All
changes via pull request") but wasn't actually being followed by dispatched
agent tasks. Flow: create a feature branch before any change → commit freely
on that branch → pushing the branch and opening the PR both require the same
per-action explicit permission as any other `git push` → Architect reviews
every PR (schema, backend, frontend, infra, devops, tests) and adds comments,
except a PR Architect itself opened, which skips straight to human review →
the human alone approves and merges; no agent ever merges any PR. Codified in
root `CLAUDE.md` ("Git Workflow", "NEVER — Session Control") and reinforced
in every agent's own `CLAUDE.md` guardrails.
*Rejected: letting agents merge their own PRs after Architect approval (removes
the human's final say on what lands on `main`), requiring Architect
self-review (no one designated to review the reviewer; human review already
covers it)*

**AWS best practices (least privilege, encryption, no hardcoded secrets) apply to every agent, not just Infra/DevOps**
2026-09-12 | User decision. Infra and DevOps already had detailed AWS-security
guardrails specific to their domain (IAM least-privilege rules, ECR
scan-on-push, OIDC over static keys). Added a general "AWS Best Practices"
section to root `CLAUDE.md`'s Universal Guardrails so every agent applies the
same principles in their own domain, plus concrete role-specific instances:
Architect (design for least-privilege data access, reference secrets via
env/Secrets Manager not literals), Backend Dev (scope boto3 calls minimally,
ask Infra for a specific permission rather than requesting a broader role),
QA (never reuse broad/admin credentials in test fixtures, prefer mocking AWS
calls over hitting real AWS in tests).
*Rejected: leaving this implicit / assuming agents infer it from Infra's
guardrails alone (Architect, Backend Dev, and QA don't read infra/CLAUDE.md
by default, so the principle needs to live where they'll actually see it)*

**Every git push and AWS CLI/SDK command is logged in `docs/CMD_LOG.md` — standing rule, no exceptions**
2026-09-12, simplified same day | User decision, given while about to run the
state-bucket setup commands. `docs/CMD_LOG.md` covers every `git push`, every
AWS CLI/SDK command, and every `terraform plan`/`apply` — i.e. every action
already gated by the "explicit permission every time" rules in root
`CLAUDE.md`. Kept deliberately minimal per user follow-up the same day: just
the commands, grouped by date, in execution order, tagged `# user` /
`# claude` — no per-entry description, context, or result fields. Committed
to git — it's an audit trail, not a secret; account IDs and credentials still
live only in the gitignored `infra/ACCOUNTS.md`.
*Rejected: relying on git log + terminal scrollback alone (scattered across
two places and loses AWS commands entirely, since those aren't git-tracked
by nature), logging in `infra/ACCOUNTS.md` (mixes a running log with a
reference doc, and that file is gitignored — the log should be committed),
a verbose per-entry format with context/result fields (user wanted it simple)*

**Every BRD update bumps the version and logs it in the BRD's own Version History table — standing rule, no exceptions**
2026-09-12, retention rule added same day | The BRD (`docs/BRD_v36_Restaurant_Platform.docx`
as of this decision) now carries a "Version History" table (Version | Date |
Changes) right after its title-page metadata. Any future edit to BRD content —
not just this one — must:
1. Bump the version number in the title-page metadata table
2. Add a new row to the Version History table describing what changed and why
3. Rename the file to match (`BRD_v<major>_Restaurant_Platform.docx`) and update
   the three references to it (`README.md`, root `CLAUDE.md`, `docs/AGENT_DESIGN.md`)
4. **Keep n-2 old version files before cleanup** — retain the current file's
   two immediately-preceding versioned `.docx` files in `docs/` (3 files on
   disk at any time: current + previous 2). Only delete the oldest kept file
   once a new bump would make a 4th file exist. Never delete an old version's
   file in the same edit that creates the new one — the deletion (if any) is a
   separate, later cleanup step once the n-2 window is exceeded.
No silent edits — the document must be able to answer "what changed and when"
from its own content, without needing git history, and old versions stay
recoverable from disk for a window rather than relying solely on git history.
*Rejected: git history as the only changelog (BRD is reviewed by stakeholders who
don't use git), a separate changelog file (splits the log from the document it
describes), deleting the previous version immediately on every bump (no
same-day fallback if the new version needs correcting)*

---

## Infrastructure & Hosting

**Region: `us-east-1`, confirmed despite DFW being the initial market**
2026-09-12 | Considered switching to a west-coast region given the DFW launch
market, but geography doesn't favor it: us-west-1/us-west-2 are farther from
Dallas than us-east-1 (Virginia), not closer, so there's no latency argument
for moving west. us-east-1 is already the default across every Terraform
module and `terraform.tfvars.example`, and it has the broadest AWS service
availability and typically the lowest pricing. No change made — confirming
the existing default rather than picking a new region.
*Rejected: us-west-1/us-west-2 (farther from Texas, no latency benefit, would
require re-plumbing every module's default), us-east-2 (marginal geographic
difference vs. us-east-1, not worth a config change for no real benefit)*

**AWS account structure: AWS Organizations member accounts, one per environment, starting with `dev` only**
2026-09-12 | User decision. New member accounts under the existing management/
payer account — consolidated billing, no separate payment method per
environment. Only `dev` is created now; `test` and `prod` follow later, added
the same way when there's something worth staging or launching. Account
creation itself is a manual step (AWS Organizations console, or
`aws organizations create-account` run by the human) — no agent creates AWS
accounts, ever (see root `CLAUDE.md` "NEVER — Session Control" and the
Prohibited-actions policy this session operates under).
*Rejected: fully standalone accounts with separate billing (no benefit over
Organizations member accounts for this use case), setting up all three
environments now (Phase 1 work only needs `dev`; test/prod would sit unused)*

**Containerization: Lambda container images via ECR, chosen for cost at low/no load**
2026-09-12 | User wants to containerize for easy promotion across environments,
and asked for the cheapest option given light load expected for months to
years. Compared against ECS Fargate and AWS App Runner:
- **Lambda (container image)** — true scale-to-zero, pay per invocation/duration,
  no VPC or NAT required. Cheapest at low/no traffic, matches the existing
  Phase cost ladder ($20-50/mo Phase 1) exactly, because it's the same pricing
  model as the zip-based Lambda already decided — only the packaging changes.
- **App Runner** — simpler ops than Fargate, but no true scale-to-zero; some
  baseline cost exists even at zero traffic.
- **ECS Fargate** — most flexible, but needs a VPC and typically a NAT Gateway
  or VPC endpoints, and tasks don't scale to zero as cleanly — highest cost
  and complexity of the three, and the NAT Gateway path directly conflicts
  with the existing "NEVER create a NAT Gateway" guardrail.
Chose Lambda container images: same Mangum/FastAPI code, packaged as a Docker
image (`backend/Dockerfile`) instead of a zip, stored in ECR, referenced by
the Lambda function's `image_uri`. Promotable across environments by pushing
the same image digest into each environment's ECR once `test`/`prod` exist.
*Rejected: App Runner (baseline cost at zero traffic), ECS Fargate (VPC/NAT
cost and complexity, guardrail conflict)*

**All infrastructure runs on AWS — no external vendors**
May 2026 | Single vendor means one bill, one IAM setup, one Terraform state.
Vercel was considered for Next.js hosting but rejected to avoid split vendor management.
*Rejected: Vercel, Netlify, Railway*

**Next.js hosted on AWS Amplify (Phase 1–2)**
May 2026 | Amplify handles Next.js SSR natively within AWS. Free tier covers Phase 1
traffic (1,000 build min/mo, 15GB served/mo). Migration trigger to App Runner:
80GB/mo bandwidth or 10,000 MAU.
*Rejected: Vercel (external vendor), App Runner (over-spec for Phase 1)*

**No Redis in Phase 1–2**
May 2026 | At Phase 1 scale (dozens of concurrent users), Redis adds cost and
operational complexity without meaningful benefit. is_paid() uses a stored boolean
(single DB read). Redis added in Phase 3 for geo search query caching only.
*Rejected: Redis from day 1 (premature optimisation)*

**No RDS Proxy in Phase 1–2**
May 2026 | Aurora Serverless v2 at Phase 1 traffic won't hit connection limits.
RDS Proxy added in Phase 3+ only when concurrent users exceed ~200.
*Rejected: RDS Proxy from day 1 (unnecessary cost ~$15-30/mo at launch)*

**Terraform for all infrastructure**
May 2026 | Version-controlled, reproducible, auditable. All AWS resources in code.
Agents generate plans only — humans apply.
*Rejected: AWS Console manual setup, AWS CDK (team prefers HCL over Python for infra)*

**Aurora PostgreSQL Serverless v2 + PostGIS (not DynamoDB)**
May 2026 | Geographic search (radius queries, multi-filter) requires relational + geo
capabilities. PostGIS ST_DWithin makes 15-mile radius queries trivial. DynamoDB has
no native geo support and would require a custom library.
Aurora Serverless v2 scales to zero (min_capacity=0) maintaining cost parity.
*Rejected: DynamoDB (no native geo), MongoDB Atlas (external vendor)*

**Single EventBridge cron rule for deal expiry (not one rule per deal)**
May 2026 | One rule per deal = thousands of rules at scale, high management complexity.
Single Lambda runs every 5 minutes:
UPDATE deal SET is_active=false WHERE is_active=true AND end_at IS NOT NULL AND end_at <= NOW()
*Rejected: Per-deal EventBridge rules (rule proliferation), SQS delay queues (complexity)*

**S3 presigned URLs for image uploads (never through Lambda)**
May 2026 | Lambda has a 6MB payload limit. Passing 5MB images through Lambda exhausts
memory and hits size limits. Presigned URL flow: client requests URL → uploads directly
to S3 → S3 event triggers resize Lambda.
*Rejected: Direct Lambda upload endpoint (hits 6MB limit)*

**AWS Amplify build, not separate CI/CD for frontend**
May 2026 | Amplify handles build + deploy + CDN in one service. GitHub Actions handles
backend and infra CI only.
*Rejected: GitHub Actions for frontend deploy (extra complexity)*

---

## Database & Data Model

**Tier stored as boolean (is_paid + paid_until) on restaurant_location**
May 2026 | No stored tier enum. is_paid is set directly by Stripe webhooks and admin
free offer grants. Single indexed boolean read per request — fast, simple, no cache needed.
Downgrade triggers immediately on first payment failure with no grace period.
*Rejected: Tier enum field (stale state risk), Redis cache (unnecessary Phase 1 complexity),
real-time Stripe API check per request (rate limits + latency)*

**Per-location billing (not per-owner)**
May 2026 | Owner can have some locations on paid and some on free simultaneously.
Granular control, clearer value proposition. Owner pays for what they use.
*Rejected: Per-owner billing (owner with 1 paid location would pay for all their locations)*

**Stripe Subscription Items model (one item per paid location)**
May 2026 | One Stripe subscription per owner with one Item per paid location.
Generates one consolidated invoice per month. is_paid() checks stripe_sub_item_id
on the location row.
*Rejected: Separate subscription per location (multiple invoices), quantity field
(loses track of which specific locations are paid)*

**owner_id nullable on restaurant_brand (unclaimed listings)**
May 2026 | Admin seeds 500 restaurants before any owner claims them. Nullable owner_id
with is_claimed=false allows unclaimed listings to exist and be searchable.
*Rejected: Placeholder admin owner account (pollutes ownership data)*

**deal type ENUM (deal | special)**
May 2026 | Both use the same table. Deals have end_at set (time-limited).
Specials have end_at=NULL (permanent until owner removes). Single table, clean query.
*Rejected: Separate specials table (unnecessary duplication)*

**Audit log on all core entity writes**
May 2026 | Full audit trail required for data governance. All writes to restaurant_brand,
restaurant_location, menu_item, deal, owner_account, location_manager logged with
actor_id, actor_role, before/after values.
*Rejected: No audit log (cannot investigate disputes or data quality issues)*

---

## Authentication & Permissions

**AWS Cognito for auth (4 groups: owner, manager, admin, registered_user)**
May 2026 | Managed auth within AWS. No separate auth vendor. Cognito handles
JWT issuance, refresh, MFA, social login.
*Rejected: Auth0 (external vendor), custom JWT (security risk, maintenance burden)*

**Manager permissions validated server-side on every write (not JWT-only)**
May 2026 | JWT TTL is 15 minutes. A removed manager's JWT stays valid until expiry.
Every write checks location_manager table directly (is_active=true).
Removal takes effect on the next request, not at JWT expiry.
*Rejected: JWT claims only (removed manager retains access up to 15 min — acceptable
for reads but not for writes)*

**Managers can initiate upgrades but only owners can downgrade**
May 2026 | Downgrade hides paid content immediately and reduces owner's invoice.
Too impactful to allow managers to trigger. Upgrades only add value so managers
can initiate (subject to owner's card being charged).
*Rejected: Manager can downgrade (rogue manager risk)*

**Manager can add card on behalf of owner**
May 2026 | Owner receives informational email when a manager adds a card. No
cancellation option — charge proceeds. Simplest UX for restaurant teams where
manager handles admin.
*Rejected: Owner-only card entry (friction when manager handles billing)*

---

## Billing & Payments

**BRD corrected to match the existing per-location billing model (was internally inconsistent)**
2026-09-12 | BRD section 3.3's intro paragraph said "tier is set at the owner
level" while its own section 4 Core Principles said "billing is per-location" —
directly contradicting each other. The per-location model was already decided
(see "Per-location billing (not per-owner)" below) and is what the schema and
Stripe design implement; the BRD's 3.3 paragraph was stale and has been fixed to
match. No design change here — just removing a documentation inconsistency.
*Rejected: nothing — this was a bug in the BRD text, not a real design choice*

**Payment failure = immediate free tier, no grace period, no retries**
May 2026 | Clean, simple, predictable. If you haven't paid, you're on free tier.
No stale paid state. No complex retry logic. Daily reconciliation Lambda catches
any missed Stripe webhooks.
*Rejected: Grace period (complex state management), Stripe retry cycle (2 weeks
of uncertainty for platform and owner)*

**Admin free offer sets is_paid=true + paid_until directly**
May 2026 | No Stripe interaction needed for admin free offers. Simple DB write.
When offer ends, is_paid reverts to false unless owner has active Stripe subscription.
Subscription clock resets after offer period.
*Rejected: Stripe coupon/discount (complex, affects invoices), Stripe pause_collection
(extra API call, unnecessary for simple free offer)*

**Pricing stored in platform_pricing table with effective dates**
May 2026 | Admin can set new price with future effective_date. System reads most
recent row where effective_date <= today. No code deploy needed for price changes.
Current pricing: $100/mo or $1,000/yr per location.
*Rejected: Hardcoded pricing (requires code deploy for price changes)*

**Owner-scoped free offer covers all their locations including new ones added during the offer**
May 2026 | Simpler than tracking which locations existed when the offer was granted.
Owner adds new location during free period — it gets the benefit too.
*Rejected: Offer only applies to locations at grant time (complex tracking)*

---

## Features & Product

**Full menu with prices moved to free tier; dish photos split out as the paid feature (BRD 3.3)**
2026-09-12 | The combined "Full menu with prices and dish photos" row (paid-only)
is split into two: seeing the full menu with prices is now free for every
location — it's core to a "genuinely useful free listing" (see Core Principles);
professional dish photography remains a paid-only feature.
*Rejected: keeping menu pricing behind the paywall (contradicts the free-tier
usefulness principle already in the BRD)*

**Photo gallery: 2 photos free, 10 photos paid per location (was 0 free / 10 paid)**
2026-09-12 | BRD 3.3's "Up to 10 photos per location" row gave free listings zero
gallery photos beyond the single cover photo. Changed to 2 free / 10 paid so free
listings have some visual presence beyond one cover shot, while still leaving a
clear upgrade incentive.
*Rejected: 0 free (too bare for a "genuinely useful" free listing), unlimited
free (removes the paid-tier incentive)*

**Assignable location managers capped at 2 per location on paid tier (was unlimited)**
2026-09-12 | BRD 3.3 previously allowed unlimited managers per paid location.
Capped at 2 to keep the owner/manager permission surface small and reviewable
for Phase 1–2 scale; revisit if a real owner needs more.
*Rejected: unlimited (no stated need for it yet, harder to reason about audit
trails and permission boundaries with an unbounded manager list)*

**No location cap for free tier**
May 2026 | Per-location billing makes the cap concept redundant. Owners can have
unlimited free locations — each one is independently free or paid. No artificial limit.
*Rejected: Cap at 2, 3, or 5 (arbitrary friction, contradicts per-location billing)*

**No follow cap for registered users**
May 2026 | 10-follow cap was intended as a freemium gate, but there is no consumer
paid tier defined. Cap creates friction with no corresponding upgrade path.
All registered users can follow unlimited restaurants.
*Rejected: 10-follow cap with consumer paid tier (adds product complexity)*

**Brand-level search results (not flat location results)**
May 2026 | A brand with 5 DFW locations would appear 5 times in flat results.
Search returns brand cards with "X locations near you" expandable.
Location-level geo query still used under the hood.
*Rejected: Flat location results (terrible UX for multi-location brands)*

**Search default sort: verified first, then distance, then alphabetical**
May 2026 | Phase 1 and 2 default. Phase 3 introduces weighted ranking
(paid + verified + recent deals). Simple and predictable for launch.
*Rejected: Random, purely alphabetical, purely distance*

**Default search radius: 15 miles**
May 2026 | Appropriate for DFW metro — covers a full suburban drive.
City search uses admin-configured bounding box. No location = city default.
*Rejected: 5 miles (too narrow for suburban US), 25 miles (too broad)*

**Deals visible to registered users only (not public)**
May 2026 | Clear incentive for public visitors to create a free account.
Registration is the gate, not payment.
*Rejected: Deals public (removes registration incentive)*

**Online ordering = redirect link model in Phase 4 (not on-platform checkout)**
May 2026 | Platform links to restaurant's own ordering system (DoorDash, their own URL).
Avoids food delivery logistics, payment processing liability, and fulfilment complexity.
Full on-platform checkout is a post-Phase 4 decision.
*Rejected: On-platform checkout in Phase 4 (too complex, too much liability)*

**No community edits — owner/manager/admin only**
May 2026 | Data quality over crowdsourcing. Prevents spam, fake reviews, competitor
sabotage. Platform maintains editorial control.
*Rejected: Yelp-style community edits (data quality risk)*

**Claim flow: Google Business Profile match OR phone verification, admin-reviewed, 2-business-day SLA**
Sep 2026 | Primary proof path: owner's Google Business Profile listing shows matching
name/address, treated as pre-verified. Fallback: outbound call to the phone number
already on the public listing (not one the claimant supplies) confirms identity.
If neither passes, claimant uploads one supporting document (business license or
utility bill) for manual admin review. Single admin queue, 2-business-day SLA for
Phase 1 volume. Unclaimed listings (owner_id NULL, is_claimed=false — see Database
section) stay visible and searchable with a "Claim this listing" CTA; nothing is
hidden while unclaimed.
*Rejected: Phone number claimant supplies (spoofable — no identity signal),
crowdsourced/community verification (contradicts no-community-edits decision),
no proof requirement (listing takeover risk)*

**Restaurant hours: structured weekly schema + display status in Phase 1, "open now" search filter deferred to Phase 3**
Sep 2026, revised 2026-09-12 | `restaurant_hours` table (location_id, day_of_week,
open_time, close_time, is_closed) captured during data seeding so it isn't a
schema migration later — cheap to add now, expensive to backfill. BRD section 3.3
lists "Open/closed status + map pin" as a baseline feature for both tiers, so
**computing and displaying open/closed status on the listing page is in Phase 1**
(it's a per-row lookup, not a search feature). What's deferred to Phase 3
(Discovery+, alongside map view and NLS search) is the `open_now` **search
filter** — i.e. `/search?open_now=true` querying across all results. Locations
without confirmed hours at seed time get is_closed=NULL ("hours unknown, call
ahead") rather than a guess.
*Rejected: No hours field until Phase 3 (forces a migration + re-seed later),
no display status in Phase 1 (contradicts BRD 3.3 baseline feature), building
the open_now search filter now (unnecessary scope for a directory-only Phase 1)*

**Data seeding: admin-curated import from public listing sources, manual verification before publish**
Sep 2026 | First ~500 DFW restaurants sourced from public business listing data
(e.g. Google Places API) for core fields only — name, address, phone, regional
cuisine tag. No scraped menus, hours default to unknown (see hours decision above).
Each seeded row is admin-reviewed and marked verified=true before it's publicly
visible, consistent with the no-community-edits / editorial-control decision.
Owners can later claim and enrich their own listing.
*Rejected: Fully automated scrape-and-publish (skips admin verification, data
quality risk), partner/restaurant self-submission for the initial 500 (too slow
to reach launch volume, no accounts exist yet)*

---

## Agent Architecture

**DevOps agent added, split from Infra**
2026-09-12 | Containerization + CI/CD (image builds, deploys, eventual
cross-account promotion once `test`/`prod` exist) is a distinct concern from
defining Terraform resources. Infra still owns the ECR repo and Lambda
function as Terraform resources; DevOps owns the pipeline that builds images
and ships them into those resources (`.github/workflows/`, build/deploy
scripts, the GitHub OIDC trust role's required permissions). See
`devops/CLAUDE.md`.
*Rejected: folding CI/CD into Infra's scope (conflates "what resources exist"
with "how code moves through them," and Infra's scope was already broad)*

**Orchestrator (Option 3) activated from Phase 1, not deferred to Phase 3 — supersedes prior decision below**
2026-09-12 | User decision: Phase 1 build work is dispatched through `orchestrator.py`
from the start, not through manually coordinated Option 2 sessions. Approval-gate
and manual-trigger-only constraints (decided earlier the same session, see
`BRD_OPEN_ITEMS.md`) still apply — the orchestrator proposes a subtask breakdown,
a human approves it, then it dispatches. Option 2 (focused sessions) remains
available for one-off work outside the task queue. See `AGENT_DESIGN.md`
Option 3 for the updated "Active: Phase 1+" spec.
*Rejected: waiting for Phase 3 as originally planned (superseded by explicit user
instruction to start now)*

**(Superseded 2026-09-12 — kept for history) Option 2 now (focused sessions), Option 3 later (orchestrator)**
May 2026 | Phases 1–2: manually coordinated Claude Code sessions per directory.
Simple, transparent, human stays in control. orchestrator.py built in Phase 3
for automated repeating tasks (add city, add feature type, data quality checks).
*Rejected: Single agent (context pollution), orchestrator from day 1 (over-engineering — reversed 2026-09-12)*

**5 CLAUDE.md files (root + 4 agents)**
May 2026 | Root: shared context for all. Agent-specific: focused skills + guardrails.
Each file is concise — not a novel. Context window is finite.
*Rejected: Single mega CLAUDE.md (too large, unfocused)*

**Architect agent activated from Phase 1 — supersedes prior decision below**
2026-09-12 | User decision, prompted by BRD section 5.1 and the Executive
Summary already listing a 6-agent roster (Orchestrator, Architect, Backend Dev,
Frontend Dev, Infra, QA) that this repo's `AGENT_DESIGN.md` hadn't matched.
Architect owns `/backend/app/models`, the initial migration per entity, and
`/docs/API_CONTRACTS.md` / `/docs/DATA_MODEL.md`. Backend Dev no longer owns
schema design. See `architect/CLAUDE.md`.
*Rejected: leaving Backend Dev to own schema design (superseded — BRD already
specified a separate Architect role, the repo just hadn't caught up)*

**(Superseded 2026-09-12 — kept for history) No separate Architect agent in Phases 1–2**
May 2026 | Backend Dev agent handles schema design because the codebase is small.
Architect becomes a dedicated agent in Phase 3+ when schema complexity warrants it.
*Rejected: Separate Architect from day 1 (unnecessary coordination overhead — reversed 2026-09-12)*

---

## Expansion & Scale

**One new city per phase (DFW → Houston → Chicago)**
May 2026 | Data seeding is the bottleneck, not code. One city at a time ensures
quality over breadth.
*Rejected: Launch all cities simultaneously (data quality risk)*

**Phase cost ladder documented**
May 2026 | Phase 1: $20-50/mo. Phase 2: $40-80/mo. Phase 3: $100-180/mo.
Phase 4: $180-350/mo. Add Redis and RDS Proxy only when traffic justifies it.
*Rejected: Full production stack from day 1 (wasteful at launch scale)*

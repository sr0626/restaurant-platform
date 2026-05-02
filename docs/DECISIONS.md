# Architecture Decision Log

Every significant technical or product decision made for this project.
Read this before asking "why did we do X?" — the answer is probably here.
When a new decision is made, add it to the top of the relevant section.

Format: **Decision** | Date | Reasoning | Alternatives Rejected

---

## Infrastructure & Hosting

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

---

## Agent Architecture

**Option 2 now (focused sessions), Option 3 later (orchestrator)**
May 2026 | Phases 1–2: manually coordinated Claude Code sessions per directory.
Simple, transparent, human stays in control. orchestrator.py built in Phase 3
for automated repeating tasks (add city, add feature type, data quality checks).
*Rejected: Single agent (context pollution), orchestrator from day 1 (over-engineering)*

**5 CLAUDE.md files (root + 4 agents)**
May 2026 | Root: shared context for all. Agent-specific: focused skills + guardrails.
Each file is concise — not a novel. Context window is finite.
*Rejected: Single mega CLAUDE.md (too large, unfocused)*

**No separate Architect agent in Phases 1–2**
May 2026 | Backend Dev agent handles schema design because the codebase is small.
Architect becomes a dedicated agent in Phase 3+ when schema complexity warrants it.
*Rejected: Separate Architect from day 1 (unnecessary coordination overhead)*

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

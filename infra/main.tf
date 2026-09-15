# -------------------------------------------------------------------
# Restaurant Platform — Phase 1 Root Module
#
# Module dependency order (Terraform resolves automatically via references):
#   networking  (no deps)
#   ses         (no deps)
#   s3          (no deps)
#   ecr         (no deps)
#   cognito     → ses
#   aurora      → networking
#   iam         → aurora, s3, ecr, cognito, (stripe secrets defined inline)
#   lambda      → networking, iam, aurora, cognito, s3, ecr (image_uri)
#   eventbridge → lambda
#   amplify     → lambda, cognito, s3
#
# Note: iam.github_actions_role_arn scopes lambda:UpdateFunctionCode to the
# API Lambda's ARN, but that ARN is constructed locally inside the iam
# module from the known naming convention rather than taken from
# module.lambda's output — module.lambda already depends on module.iam for
# execution role ARNs, so the reverse reference would be a circular module
# dependency (see infra/modules/iam/github_actions.tf).
# -------------------------------------------------------------------

data "aws_caller_identity" "current" {}

# -------------------------------------------------------------------
# Networking — VPC, private subnets, SGs, VPC endpoints
# No NAT Gateway; Lambda reaches AWS services via VPC endpoints only.
# -------------------------------------------------------------------
module "networking" {
  source = "./modules/networking"

  env        = var.env
  project    = var.project
  phase      = var.phase
  aws_region = var.aws_region
}

# SES deferred — modules/ses/ scaffold is written; wire it back in when needed.

# -------------------------------------------------------------------
# S3 — private media bucket + CloudFront OAC distribution
# -------------------------------------------------------------------
module "s3" {
  source = "./modules/s3"

  env        = var.env
  project    = var.project
  phase      = var.phase
  aws_region = var.aws_region
}

# -------------------------------------------------------------------
# ECR — backend API container image repository (added 2026-09-12, see
# DECISIONS.md "Containerization"). Building/pushing images is DevOps's
# job; Terraform only owns the repo resource.
#
# service_name = "api" is explicit here (matches the module's own default)
# per DECISIONS.md "Multi-service scaling" — a second service later is a
# second `module "ecr"` block below with a different service_name, not a
# rename of this one.
# -------------------------------------------------------------------
module "ecr" {
  source = "./modules/ecr"

  env          = var.env
  project      = var.project
  phase        = var.phase
  service_name = "api"
}

# -------------------------------------------------------------------
# Cognito — User Pool with 4 groups; transactional email via SES
# -------------------------------------------------------------------
module "cognito" {
  source = "./modules/cognito"

  env     = var.env
  project = var.project
  phase   = var.phase
}

# -------------------------------------------------------------------
# Aurora Serverless v2 — PostgreSQL 15, min=0 (scale to zero)
# PostGIS enabled via Alembic migration — NOT provisioned here.
# -------------------------------------------------------------------
module "aurora" {
  source = "./modules/aurora"

  env          = var.env
  project      = var.project
  phase        = var.phase
  aws_region   = var.aws_region
  db_username  = var.db_username
  max_capacity = var.aurora_max_capacity

  vpc_id       = module.networking.vpc_id
  subnet_ids   = module.networking.private_subnet_ids
  lambda_sg_id = module.networking.lambda_sg_id
}

# -------------------------------------------------------------------
# Phase-2 Secrets Manager placeholders — pre-provision slots only.
# Populate with real Stripe values before Phase 2 activation.
# -------------------------------------------------------------------
resource "aws_secretsmanager_secret" "stripe_secret_key" {
  name                    = "${var.project}/${var.env}/STRIPE_SECRET_KEY"
  description             = "Stripe secret API key — Phase 2 placeholder"
  recovery_window_in_days = var.env == "prod" ? 30 : 0

  tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

resource "aws_secretsmanager_secret_version" "stripe_secret_key" {
  secret_id     = aws_secretsmanager_secret.stripe_secret_key.id
  secret_string = "PLACEHOLDER — update with real Stripe secret key before Phase 2"
}

resource "aws_secretsmanager_secret" "stripe_webhook_secret" {
  name                    = "${var.project}/${var.env}/STRIPE_WEBHOOK_SECRET"
  description             = "Stripe webhook signing secret — Phase 2 placeholder"
  recovery_window_in_days = var.env == "prod" ? 30 : 0

  tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

resource "aws_secretsmanager_secret_version" "stripe_webhook_secret" {
  secret_id     = aws_secretsmanager_secret.stripe_webhook_secret.id
  secret_string = "PLACEHOLDER — update with real Stripe webhook secret before Phase 2"
}

# -------------------------------------------------------------------
# IAM — least-privilege execution roles; one per Lambda
# -------------------------------------------------------------------
module "iam" {
  source = "./modules/iam"

  env        = var.env
  project    = var.project
  phase      = var.phase
  aws_region = var.aws_region
  account_id = data.aws_caller_identity.current.account_id

  # service_name = "api" matches module.ecr / module.lambda's own service_name
  # below — scopes github_actions.tf's local.api_lambda_arn to this Lambda.
  service_name = "api"

  media_bucket_arn          = module.s3.media_bucket_arn
  db_secret_arn             = module.aurora.db_secret_arn
  stripe_secret_key_arn     = aws_secretsmanager_secret.stripe_secret_key.arn
  stripe_webhook_secret_arn = aws_secretsmanager_secret.stripe_webhook_secret.arn
  ecr_repository_arn        = module.ecr.repository_arn
  github_repo_url           = var.github_repo_url
  cognito_user_pool_arn     = module.cognito.user_pool_arn
}

# -------------------------------------------------------------------
# Lambda — API (Mangum/FastAPI, container image) + deal-expiry (zip);
# both in private subnets.
#
# `lambda_image_uri` bootstrap/CI-CD tension (flagged for review):
# `aws_lambda_function.api` requires an image that already exists in ECR at
# create time, but `module.ecr` starts out empty on a brand-new environment
# — a real chicken-and-egg problem, not something Terraform code alone can
# resolve. Resolved by defaulting to the repo's own `:bootstrap` tag rather
# than `:latest`: IMMUTABLE tag mutability (module.ecr) means a tag can only
# ever be pushed once, so `:latest` — a tag implicitly meant to be
# overwritten — doesn't fit that policy, while a `:bootstrap` tag pushed
# manually ONE TIME before the very first `terraform apply` does.
#
# Required one-time manual step before the first apply of a new environment
# (human runs this — not Terraform, not this agent):
#   docker pull public.ecr.aws/docker/library/hello-world:latest
#   docker tag public.ecr.aws/docker/library/hello-world:latest \
#     <module.ecr.repository_url output>:bootstrap
#   docker push <module.ecr.repository_url output>:bootstrap
# After that, DevOps's pipeline pushes real per-commit-SHA tags and moves
# the running Lambda onto them via `aws lambda update-function-code`
# (devops/CLAUDE.md) — never via `terraform apply` again. The
# `lifecycle.ignore_changes = [image_uri]` in modules/lambda/main.tf is what
# stops `terraform plan` from then wanting to revert those deploys back to
# `:bootstrap`. `var.lambda_image_uri` (root, optional) can override this
# default if a different bootstrap tag/digest is used.
# -------------------------------------------------------------------
locals {
  lambda_image_uri = coalesce(var.lambda_image_uri, "${module.ecr.repository_url}:bootstrap")
}

module "lambda" {
  source = "./modules/lambda"

  env        = var.env
  project    = var.project
  phase      = var.phase
  aws_region = var.aws_region

  # service_name = "api" is explicit here (matches the module's own default)
  # per DECISIONS.md "Multi-service scaling" — a second service later is a
  # second `module "lambda"` block below with a different service_name.
  # Does not affect the deal-expiry Lambda in this same module (single
  # cross-service cron job) or the shared API Gateway resource.
  service_name = "api"

  vpc_id       = module.networking.vpc_id
  subnet_ids   = module.networking.private_subnet_ids
  lambda_sg_id = module.networking.lambda_sg_id

  api_lambda_role_arn         = module.iam.api_lambda_role_arn
  deal_expiry_lambda_role_arn = module.iam.deal_expiry_lambda_role_arn
  lambda_image_uri            = local.lambda_image_uri

  db_secret_name       = module.aurora.db_secret_name
  media_bucket_name    = module.s3.media_bucket_name
  cognito_user_pool_id = module.cognito.user_pool_id
  allowed_origins      = var.allowed_origins
}

# -------------------------------------------------------------------
# EventBridge Scheduler — deal expiry cron (rate 5 min)
# Single rule — NOT one per deal; Lambda scans all expired deals.
# -------------------------------------------------------------------
module "eventbridge" {
  source = "./modules/eventbridge"

  env        = var.env
  project    = var.project
  phase      = var.phase
  aws_region = var.aws_region

  deal_expiry_lambda_arn  = module.lambda.deal_expiry_lambda_arn
  deal_expiry_lambda_name = module.lambda.deal_expiry_lambda_name
}

# -------------------------------------------------------------------
# Amplify — Next.js 14 (App Router / SSR) hosted frontend
# GitHub repo: https://github.com/sr0626/swarasa
# -------------------------------------------------------------------
module "amplify" {
  source = "./modules/amplify"

  env     = var.env
  project = var.project
  phase   = var.phase

  github_repo_url     = var.github_repo_url
  github_access_token = var.github_access_token

  api_gateway_url      = module.lambda.api_gateway_url
  cognito_user_pool_id = module.cognito.user_pool_id
  cognito_client_id    = module.cognito.client_id
  cloudfront_url       = "https://${module.s3.cloudfront_domain}"
}

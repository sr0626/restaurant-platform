variable "env" {
  description = "Environment name: dev, staging, prod"
  type        = string
}

variable "project" {
  description = "Project name for tagging"
  type        = string
  default     = "swarasa"
}

variable "phase" {
  description = "Project phase for tagging"
  type        = string
  default     = "phase1"
}

variable "service_name" {
  description = <<-EOT
    Service identifier used in the API-style Lambda's naming:
    "$${project}-$${service_name}-$${env}". Defaults to "api" so the existing
    single-service call site (module "lambda" in root main.tf) is
    unaffected. A second service later is a second `module "lambda"` block
    with a different service_name — see DECISIONS.md "Multi-service
    scaling" — not a redesign of this module. Does NOT affect the
    deal-expiry Lambda (a single cross-service cron job, not per-service) or
    the shared API Gateway resource.
  EOT
  type        = string
  default     = "api"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Lambda VPC configuration"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for Lambda functions"
  type        = list(string)
}

variable "lambda_sg_id" {
  description = "Security group ID for Lambda functions"
  type        = string
}

variable "api_lambda_role_arn" {
  description = "IAM execution role ARN for the API Lambda"
  type        = string
}

variable "lambda_image_uri" {
  description = <<-EOT
    Full ECR image URI for the API Lambda's container image
    (<repository_url>:<tag> or <repository_url>@<digest>).

    Terraform/CI-CD boundary: DevOps's pipeline is what moves this forward in
    the running Lambda on every merge to main, via `aws lambda
    update-function-code` (devops/CLAUDE.md) — not by re-running `terraform
    apply` with a new value here. `aws_lambda_function.api` has
    `lifecycle.ignore_changes = [image_uri]` so a stale value passed into
    this variable never fights DevOps's deploys on a later `terraform plan`.
    This variable's value only matters the first time the function is
    created, before which the referenced image must already exist in ECR
    (the root module defaults it to the ECR repo's `:bootstrap` tag — see
    the root `main.tf` comment on `module "lambda"` for the one-time manual
    push this requires before the very first apply).
  EOT
  type        = string
}

variable "deal_expiry_lambda_role_arn" {
  description = "IAM execution role ARN for the deal-expiry Lambda"
  type        = string
}

variable "db_secret_name" {
  description = "Secrets Manager secret name for DB credentials (read at cold start)"
  type        = string
}

variable "media_bucket_name" {
  description = "S3 media bucket name"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for JWT verification"
  type        = string
}

variable "allowed_origins" {
  description = "CORS allowed origins for API Gateway"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

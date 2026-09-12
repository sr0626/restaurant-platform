variable "env" {
  description = "Environment name: dev, staging, prod"
  type        = string
}

variable "project" {
  description = "Project name for tagging"
  type        = string
  default     = "restaurant-platform"
}

variable "phase" {
  description = "Project phase for tagging"
  type        = string
  default     = "phase1"
}

variable "aws_region" {
  description = "AWS region — used to construct ARNs in IAM policy documents"
  type        = string
}

variable "account_id" {
  description = "AWS account ID — used to construct ARNs in IAM policy documents"
  type        = string
}

variable "media_bucket_arn" {
  description = "S3 media bucket ARN — grants API Lambda put/get/delete"
  type        = string
}

variable "db_secret_arn" {
  description = "Secrets Manager ARN for DB credentials — grants both Lambdas GetSecretValue"
  type        = string
}

variable "stripe_secret_key_arn" {
  description = "Secrets Manager ARN for Stripe secret key (Phase 2 placeholder)"
  type        = string
}

variable "stripe_webhook_secret_arn" {
  description = "Secrets Manager ARN for Stripe webhook secret (Phase 2 placeholder)"
  type        = string
}


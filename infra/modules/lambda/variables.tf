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

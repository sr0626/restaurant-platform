variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "env" {
  description = "Deployment environment: dev | staging | prod"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod"
  }
}

variable "project" {
  description = "Project name used in resource names and tags"
  type        = string
  default     = "restaurant-platform"
}

variable "phase" {
  description = "Project phase for tagging"
  type        = string
  default     = "phase1"
}

variable "db_username" {
  description = "Aurora PostgreSQL master username"
  type        = string
  default     = "restaurantadmin"
}

variable "github_repo_url" {
  description = "GitHub HTTPS URL for Amplify to clone (e.g. https://github.com/org/repo)"
  type        = string
}

variable "github_access_token" {
  description = "GitHub personal access token for Amplify — use TF_VAR_github_access_token env var"
  type        = string
  sensitive   = true
}

variable "allowed_origins" {
  description = "CORS allowed origins for API Gateway HTTP API"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "aurora_max_capacity" {
  description = "Aurora Serverless v2 max ACU (must not exceed 8 without approval)"
  type        = number
  default     = 4
  validation {
    condition     = var.aurora_max_capacity <= 8
    error_message = "aurora_max_capacity must not exceed 8 without explicit approval"
  }
}

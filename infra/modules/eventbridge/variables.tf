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

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "deal_expiry_lambda_arn" {
  description = "ARN of the deal-expiry Lambda function to invoke"
  type        = string
}

variable "deal_expiry_lambda_name" {
  description = "Name of the deal-expiry Lambda (used to scope IAM policy)"
  type        = string
}

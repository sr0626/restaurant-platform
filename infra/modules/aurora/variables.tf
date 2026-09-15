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

variable "db_username" {
  description = "Aurora master username"
  type        = string
  default     = "restaurantadmin"
}

variable "max_capacity" {
  description = "Aurora Serverless v2 max ACU — must not exceed 8 without approval"
  type        = number
  default     = 4
}

variable "vpc_id" {
  description = "VPC ID for Aurora subnet group and security group"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for Aurora (minimum 2 AZs required)"
  type        = list(string)
}

variable "lambda_sg_id" {
  description = "Lambda security group ID — granted inbound 5432 access to Aurora"
  type        = string
}

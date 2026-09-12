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


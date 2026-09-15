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
    Service identifier used in resource naming: "$${project}-$${service_name}-$${env}".
    Defaults to "api" so the existing single-service call site (module "ecr"
    in root main.tf) is unaffected. A second service later is a second
    `module "ecr"` block with a different service_name — see DECISIONS.md
    "Multi-service scaling" — not a redesign of this module.
  EOT
  type        = string
  default     = "api"
}

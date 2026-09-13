locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

# -------------------------------------------------------------------
# ECR — backend API container image repository (see DECISIONS.md
# "Containerization: Lambda container images via ECR" and infra/CLAUDE.md
# "ECR"). One repo, IMMUTABLE tags so a pushed tag can never be silently
# overwritten (a deploy is always reproducible/promotable — see
# devops/CLAUDE.md "ALWAYS tag images immutably"), scan_on_push so every
# pushed image is scanned before DevOps's pipeline treats a deploy as good.
#
# Building and pushing images is DevOps's job (devops/CLAUDE.md,
# .github/workflows/deploy-backend.yml) — Terraform only owns the repo
# resource itself, never an image inside it.
# -------------------------------------------------------------------
resource "aws_ecr_repository" "api" {
  name                 = "${var.project}-${var.service_name}-${var.env}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# Expire untagged images (dangling layers left behind when a tag is
# re-pointed at a new digest, or a failed/aborted push) after 14 days.
# Tagged images are never touched by this rule — IMMUTABLE tags plus no
# tagged-image expiry means every tag DevOps has ever pushed stays
# retrievable indefinitely (promotion/rollback safety).
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Expire untagged images after 14 days"
      selection = {
        tagStatus   = "untagged"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 14
      }
      action = { type = "expire" }
    }]
  })
}

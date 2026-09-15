terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Pre-created (2026-09-15, account 091823298313 "swarasa-dev" — this
  # account replaced the earlier "restaurant-platform-dev" account, which
  # is being removed):
  #   aws s3 mb s3://swarasa-tfstate-sr0626 --region us-east-1
  #   aws s3api put-bucket-versioning --bucket swarasa-tfstate-sr0626 \
  #       --versioning-configuration Status=Enabled
  #   aws dynamodb create-table --table-name swarasa-tfstate-lock \
  #       --attribute-definitions AttributeName=LockID,AttributeType=S \
  #       --key-schema AttributeName=LockID,KeyType=HASH \
  #       --billing-mode PAY_PER_REQUEST --region us-east-1
  #
  # State key follows the environment promotion convention (see
  # infra/CLAUDE.md "Environment promotion convention" and
  # DECISIONS.md "Terraform environment promotion"): envs/<env>/terraform.tfstate,
  # one key per environment, never a forked codebase. `dev` is the only
  # environment that exists today.
  #
  # No migration needed: `terraform apply` has never been run against any
  # backend, so this bucket/table start empty — this is a fresh account and
  # a fresh state store, not a rename of the old one.
  backend "s3" {
    bucket         = "swarasa-tfstate-sr0626"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "swarasa-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project    = var.project
      phase      = var.phase
      managed_by = "terraform"
    }
  }
}

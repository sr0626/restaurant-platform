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

  # Pre-create before first `terraform init`:
  #   aws s3 mb s3://restaurant-platform-tfstate-sr0626 --region us-east-1
  #   aws s3api put-bucket-versioning --bucket restaurant-platform-tfstate-sr0626 \
  #       --versioning-configuration Status=Enabled
  #   aws dynamodb create-table --table-name restaurant-platform-tfstate-lock \
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
  # *** HUMAN ACTION REQUIRED BEFORE THIS TAKES EFFECT — DO NOT SKIP ***
  # This key was previously "phase1/terraform.tfstate" (a placeholder from
  # before the promotion convention was decided). Changing the key here is
  # ONLY a code/config change — it does NOT move the existing remote state
  # object in S3. Terraform will NOT find prior state at the new key on its
  # own. Before running `terraform plan`/`apply` against this backend again,
  # a human must migrate the existing state, e.g.:
  #   terraform init -migrate-state
  # (when prompted, confirm copying "phase1/terraform.tfstate" to
  # "envs/dev/terraform.tfstate"), or equivalently:
  #   aws s3 cp s3://restaurant-platform-tfstate-sr0626/phase1/terraform.tfstate \
  #     s3://restaurant-platform-tfstate-sr0626/envs/dev/terraform.tfstate
  # followed by `terraform init -reconfigure`. Verify with `terraform plan`
  # showing NO changes (a clean diff) before treating the migration as done.
  # Applying against the wrong key, or skipping this step, can make Terraform
  # think all Phase 1 resources need to be recreated from scratch — this
  # agent has NOT run this migration and NEVER runs terraform init/apply
  # against real state; a human must perform this step.
  backend "s3" {
    bucket         = "restaurant-platform-tfstate-sr0626"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "restaurant-platform-tfstate-lock"
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

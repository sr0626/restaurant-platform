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
  backend "s3" {
    bucket         = "restaurant-platform-tfstate-sr0626"
    key            = "phase1/terraform.tfstate"
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

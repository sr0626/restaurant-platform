locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

# -------------------------------------------------------------------
# IAM role — allows EventBridge Scheduler to invoke the deal-expiry Lambda
# -------------------------------------------------------------------
resource "aws_iam_role" "scheduler" {
  name = "${var.project}-eb-scheduler-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })

  tags = local.common_tags
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy" "scheduler_invoke" {
  name = "${var.project}-eb-scheduler-invoke-${var.env}"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "InvokeDealExpiryLambda"
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = var.deal_expiry_lambda_arn
    }]
  })
}

# -------------------------------------------------------------------
# EventBridge Scheduler — single rule, NOT one per deal.
# Runs every 5 minutes; Lambda scans for expired deals and updates is_paid.
# -------------------------------------------------------------------
resource "aws_scheduler_schedule" "deal_expiry" {
  name       = "${var.project}-deal-expiry-${var.env}"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "rate(5 minutes)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = var.deal_expiry_lambda_arn
    role_arn = aws_iam_role.scheduler.arn

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}

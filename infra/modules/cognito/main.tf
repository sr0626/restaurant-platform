locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

# -------------------------------------------------------------------
# Cognito User Pool
# COGNITO_DEFAULT: built-in mailer, 50 emails/day — sufficient for Phase 1.
# Switch to DEVELOPER + SES module when approaching that limit.
# -------------------------------------------------------------------
resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-${var.env}"

  # Users sign themselves up; admin verification not required for Phase 1
  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  # Auto-verify email on sign-up
  auto_verified_attributes = ["email"]

  username_attributes = ["email"]

  password_policy {
    minimum_length                   = 8
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # Custom attribute: role — set by post-confirmation Lambda or admin
  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true
    required            = false

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # MFA off for Phase 1 MVP; enable OPTIONAL in Phase 2
  mfa_configuration = "OFF"

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = local.common_tags
}

# -------------------------------------------------------------------
# User groups — map to permission model (owner, manager, admin, registered_user)
# -------------------------------------------------------------------
resource "aws_cognito_user_group" "owner" {
  name         = "owner"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Restaurant owners — full access to their brands and locations"
}

resource "aws_cognito_user_group" "manager" {
  name         = "manager"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Location managers — access to explicitly assigned locations only"
}

resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Platform admins — full access"
}

resource "aws_cognito_user_group" "registered_user" {
  name         = "registered_user"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Registered consumers — read-only, follow, deals"
}

# -------------------------------------------------------------------
# Web app client — no secret (frontend/SPA cannot securely store a secret)
# -------------------------------------------------------------------
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project}-web-${var.env}"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  # Token validity
  access_token_validity  = 1    # hours
  id_token_validity      = 1    # hours
  refresh_token_validity = 30   # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"
}

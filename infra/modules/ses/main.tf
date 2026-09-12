locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

# -------------------------------------------------------------------
# SES email identity — triggers a verification email to ses_from_address.
# The identity remains unverified until the link in that email is clicked.
#
# NOTE: SES starts in sandbox mode. Only verified addresses can receive mail
# in sandbox. Request production access via AWS Console → SES → Account dashboard
# before going live.
# -------------------------------------------------------------------
resource "aws_ses_email_identity" "main" {
  email = var.ses_from_address
}

# -------------------------------------------------------------------
# SES configuration set — TLS required; reputation metrics enabled
# Pass ConfigurationSetName in ses.send_email() calls from Lambda.
# -------------------------------------------------------------------
resource "aws_ses_configuration_set" "main" {
  name = "${var.project}-${var.env}"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
  sending_enabled            = true
}

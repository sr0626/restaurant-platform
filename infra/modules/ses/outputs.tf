output "email_identity_arn" {
  description = "SES email identity ARN — used by Cognito and Lambda IAM policies"
  value       = aws_ses_email_identity.main.arn
}

output "configuration_set_name" {
  description = "SES configuration set name"
  value       = aws_ses_configuration_set.main.name
}

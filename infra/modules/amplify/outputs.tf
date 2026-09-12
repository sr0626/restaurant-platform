output "app_id" {
  description = "Amplify app ID"
  value       = aws_amplify_app.frontend.id
}

output "app_url" {
  description = "Amplify default domain URL"
  value       = "https://main.${aws_amplify_app.frontend.default_domain}"
}

output "app_arn" {
  description = "Amplify app ARN"
  value       = aws_amplify_app.frontend.arn
}

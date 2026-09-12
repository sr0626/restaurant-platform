output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "client_id" {
  description = "Cognito web app client ID (no secret — safe for frontend)"
  value       = aws_cognito_user_pool_client.web.id
}

output "user_pool_endpoint" {
  description = "Cognito User Pool endpoint (used as JWT issuer)"
  value       = aws_cognito_user_pool.main.endpoint
}

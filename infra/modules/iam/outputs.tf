output "api_lambda_role_arn" {
  description = "IAM execution role ARN for the API Lambda"
  value       = aws_iam_role.api_lambda.arn
}

output "api_lambda_role_name" {
  description = "IAM execution role name for the API Lambda"
  value       = aws_iam_role.api_lambda.name
}

output "deal_expiry_lambda_role_arn" {
  description = "IAM execution role ARN for the deal-expiry Lambda"
  value       = aws_iam_role.deal_expiry_lambda.arn
}

output "deal_expiry_lambda_role_name" {
  description = "IAM execution role name for the deal-expiry Lambda"
  value       = aws_iam_role.deal_expiry_lambda.name
}

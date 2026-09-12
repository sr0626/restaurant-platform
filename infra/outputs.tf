output "api_gateway_url" {
  description = "API Gateway HTTP API invoke URL"
  value       = module.lambda.api_gateway_url
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito web app client ID"
  value       = module.cognito.client_id
}

output "media_bucket_name" {
  description = "S3 media bucket name"
  value       = module.s3.media_bucket_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain for media delivery"
  value       = module.s3.cloudfront_domain
}

output "amplify_app_url" {
  description = "Amplify default domain URL for the frontend"
  value       = module.amplify.app_url
}

output "aurora_cluster_endpoint" {
  description = "Aurora cluster write endpoint (sensitive)"
  value       = module.aurora.cluster_endpoint
  sensitive   = true
}

output "db_secret_arn" {
  description = "Secrets Manager ARN for DB connection credentials"
  value       = module.aurora.db_secret_arn
}

output "deal_expiry_lambda_arn" {
  description = "ARN of the deal-expiry Lambda function"
  value       = module.lambda.deal_expiry_lambda_arn
}

output "api_lambda_role_arn" {
  description = "IAM execution role ARN for API Lambda"
  value       = module.iam.api_lambda_role_arn
}

output "ecr_repository_url" {
  description = "ECR repository URL for the backend API image (docker push target)"
  value       = module.ecr.repository_url
}

output "ecr_repository_arn" {
  description = "ECR repository ARN for the backend API image"
  value       = module.ecr.repository_arn
}

output "github_actions_role_arn" {
  description = "IAM role ARN DevOps's GitHub Actions pipeline assumes via OIDC — set this as the GitHub repo secret DEV_DEPLOY_ROLE_ARN referenced in devops/CLAUDE.md's deploy-backend.yml"
  value       = module.iam.github_actions_role_arn
}

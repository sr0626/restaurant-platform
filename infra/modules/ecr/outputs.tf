output "repository_url" {
  description = "ECR repository URL (push/pull target, e.g. for `docker push <repository_url>:<tag>`)"
  value       = aws_ecr_repository.api.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN — used to scope the GitHub Actions IAM role's ECR permissions to this repo only"
  value       = aws_ecr_repository.api.arn
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.api.name
}

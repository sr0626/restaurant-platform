output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for Lambda and Aurora"
  value       = aws_subnet.private[*].id
}

output "lambda_sg_id" {
  description = "Lambda security group ID"
  value       = aws_security_group.lambda.id
}

output "vpc_endpoint_sg_id" {
  description = "VPC interface endpoint security group ID"
  value       = aws_security_group.vpc_endpoints.id
}

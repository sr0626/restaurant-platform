output "api_gateway_url" {
  description = "API Gateway HTTP API invoke URL (base URL, append /path)"
  value       = "${aws_apigatewayv2_stage.default.invoke_url}"
}

output "api_gateway_id" {
  description = "API Gateway HTTP API ID"
  value       = aws_apigatewayv2_api.main.id
}

output "api_lambda_arn" {
  description = "API Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "api_lambda_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "deal_expiry_lambda_arn" {
  description = "Deal-expiry Lambda function ARN"
  value       = aws_lambda_function.deal_expiry.arn
}

output "deal_expiry_lambda_name" {
  description = "Deal-expiry Lambda function name"
  value       = aws_lambda_function.deal_expiry.function_name
}

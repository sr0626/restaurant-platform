locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }

  api_function_name          = "${var.project}-api-${var.env}"
  deal_expiry_function_name  = "${var.project}-deal-expiry-${var.env}"
}

# -------------------------------------------------------------------
# Placeholder zips — replaced by CI/CD pipeline after initial provision.
# lifecycle.ignore_changes ensures Terraform does not overwrite code
# that CI/CD has deployed.
# -------------------------------------------------------------------
data "archive_file" "api_placeholder" {
  type        = "zip"
  output_path = "/tmp/${var.project}-api-placeholder.zip"

  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'placeholder'}\n"
    filename = "placeholder.py"
  }
}

data "archive_file" "deal_expiry_placeholder" {
  type        = "zip"
  output_path = "/tmp/${var.project}-deal-expiry-placeholder.zip"

  source {
    content  = "def handler(event, context): print('deal expiry placeholder')\n"
    filename = "placeholder.py"
  }
}

# -------------------------------------------------------------------
# CloudWatch Log Groups — created explicitly so Lambda role needs no
# logs:CreateLogGroup permission and retention is enforced.
# -------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.api_function_name}"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "deal_expiry" {
  name              = "/aws/lambda/${local.deal_expiry_function_name}"
  retention_in_days = 30

  tags = local.common_tags
}

# -------------------------------------------------------------------
# API Lambda — FastAPI via Mangum handler
# -------------------------------------------------------------------
resource "aws_lambda_function" "api" {
  function_name    = local.api_function_name
  runtime          = "python3.12"
  handler          = "app.main.handler"
  role             = var.api_lambda_role_arn
  filename         = data.archive_file.api_placeholder.output_path
  source_code_hash = data.archive_file.api_placeholder.output_base64sha256
  timeout          = 30
  memory_size      = 512

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }

  environment {
    variables = {
      ENVIRONMENT          = var.env
      DB_SECRET_NAME       = var.db_secret_name
      S3_MEDIA_BUCKET      = var.media_bucket_name
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
    }
  }

  depends_on = [aws_cloudwatch_log_group.api]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = local.common_tags
}

# -------------------------------------------------------------------
# Deal-expiry Lambda — single EventBridge cron target; runs every 5 min
# -------------------------------------------------------------------
resource "aws_lambda_function" "deal_expiry" {
  function_name    = local.deal_expiry_function_name
  runtime          = "python3.12"
  handler          = "deal_expiry.handler"
  role             = var.deal_expiry_lambda_role_arn
  filename         = data.archive_file.deal_expiry_placeholder.output_path
  source_code_hash = data.archive_file.deal_expiry_placeholder.output_base64sha256
  timeout          = 60
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }

  environment {
    variables = {
      ENVIRONMENT    = var.env
      DB_SECRET_NAME = var.db_secret_name
    }
  }

  depends_on = [aws_cloudwatch_log_group.deal_expiry]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = local.common_tags
}

# -------------------------------------------------------------------
# API Gateway HTTP API
# -------------------------------------------------------------------
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project}-${var.env}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type"]
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "api_lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

# Allow API Gateway to invoke the API Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

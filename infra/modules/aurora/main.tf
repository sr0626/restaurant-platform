locals {
  common_tags = {
    project     = var.project
    environment = var.env
    phase       = var.phase
    managed_by  = "terraform"
  }
}

resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# -------------------------------------------------------------------
# DB subnet group — private subnets only; 2 AZs required by Aurora
# -------------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name        = "${var.project}-db-subnet-${var.env}"
  description = "Aurora private subnets — no public access"
  subnet_ids  = var.subnet_ids

  tags = local.common_tags
}

# -------------------------------------------------------------------
# Security group: Aurora
# Accepts connections from Lambda SG only. Port 5432 NEVER open to 0.0.0.0/0.
# -------------------------------------------------------------------
resource "aws_security_group" "rds" {
  name        = "${var.project}-rds-sg-${var.env}"
  description = "Aurora — inbound PostgreSQL from Lambda SG only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.lambda_sg_id]
  }

  tags = merge(local.common_tags, { Name = "${var.project}-rds-sg-${var.env}" })
}

# -------------------------------------------------------------------
# Aurora Serverless v2 cluster — PostgreSQL 15
# engine_mode = "provisioned" is required for Serverless v2.
# min_capacity = 0 MUST remain 0 (scales to zero when idle).
# -------------------------------------------------------------------
resource "aws_rds_cluster" "main" {
  cluster_identifier     = "${var.project}-${var.env}"
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = "15.4"
  database_name          = "restaurantdb"
  master_username        = var.db_username
  master_password        = random_password.db.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = var.env != "prod"
  deletion_protection = var.env == "prod"

  serverlessv2_scaling_configuration {
    min_capacity = 0              # MUST be 0 — scales to zero when idle
    max_capacity = var.max_capacity
  }

  tags = local.common_tags
}

resource "aws_rds_cluster_instance" "main" {
  identifier         = "${var.project}-${var.env}-1"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  tags = local.common_tags
}

# -------------------------------------------------------------------
# Secrets Manager — DB connection credentials
# Lambda reads this at cold start to construct the SQLAlchemy URL.
# PostGIS is enabled via Alembic migration (CREATE EXTENSION postgis) — not here.
# -------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.project}/${var.env}/db"
  description             = "Aurora PostgreSQL connection credentials"
  recovery_window_in_days = var.env == "prod" ? 30 : 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    host     = aws_rds_cluster.main.endpoint
    port     = 5432
    dbname   = "restaurantdb"
    engine   = "aurora-postgresql"
  })
}

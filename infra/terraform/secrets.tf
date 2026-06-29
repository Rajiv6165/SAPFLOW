# secrets.tf

# 1. Database URL Secret
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project_name}/database-url"
  recovery_window_in_days = 0

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://sapflow:${var.db_password}@${aws_db_instance.postgres.endpoint}/sapflow"
}

# 2. Redis URL Secret
resource "aws_secretsmanager_secret" "redis_url" {
  name                    = "${var.project_name}/redis-url"
  recovery_window_in_days = 0

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  secret_id     = aws_secretsmanager_secret.redis_url.id
  secret_string = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}

# 3. GitHub Token Secret
resource "aws_secretsmanager_secret" "github_token" {
  name                    = "${var.project_name}/github-token"
  recovery_window_in_days = 0

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "github_token" {
  secret_id     = aws_secretsmanager_secret.github_token.id
  secret_string = var.github_token
}

# 4. GitHub Webhook Secret
resource "aws_secretsmanager_secret" "github_webhook_secret" {
  name                    = "${var.project_name}/github-webhook-secret"
  recovery_window_in_days = 0

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "github_webhook_secret" {
  secret_id     = aws_secretsmanager_secret.github_webhook_secret.id
  secret_string = var.github_webhook_secret
}

# 5. SNS Topic ARN Secret
resource "aws_secretsmanager_secret" "sns_topic_arn" {
  name                    = "${var.project_name}/aws-sns-topic-arn"
  recovery_window_in_days = 0

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "sns_topic_arn" {
  secret_id     = aws_secretsmanager_secret.sns_topic_arn.id
  secret_string = aws_sns_topic.alerts.arn
}

# outputs.tf

output "alb_dns_name" {
  value       = aws_lb.alb.dns_name
  description = "Public URL of the load balancer"
}

output "ecr_backend_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "ECR URL for backend image"
}

output "ecr_frontend_url" {
  value       = aws_ecr_repository.frontend.repository_url
  description = "ECR URL for frontend image"
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "RDS host for connection string"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "Redis endpoint"
}

output "sns_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS topic ARN for alerts"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name"
}

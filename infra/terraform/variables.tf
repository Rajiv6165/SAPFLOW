variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS region for provisioning resources"
}

variable "project_name" {
  type        = string
  default     = "sapflow"
  description = "Project name tag and prefix"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Deployment environment"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Password for the RDS PostgreSQL database"
}

variable "github_token" {
  type        = string
  sensitive   = true
  description = "GitHub Personal Access Token for sync service"
}

variable "github_webhook_secret" {
  type        = string
  sensitive   = true
  description = "Secret used to verify GitHub webhook signatures"
}

variable "alert_email" {
  type        = string
  description = "Email for CloudWatch SNS alerts"
}

variable "backend_image" {
  type        = string
  description = "ECR image URI for backend container"
}

variable "frontend_image" {
  type        = string
  description = "ECR image URI for frontend container"
}

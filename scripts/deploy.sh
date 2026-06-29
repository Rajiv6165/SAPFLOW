#!/bin/bash
set -e

# Ensure environment variables are set
if [ -z "$AWS_REGION" ] || [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$ECR_BACKEND" ] || [ -z "$ECR_FRONTEND" ]; then
  echo "❌ Error: AWS_REGION, AWS_ACCOUNT_ID, ECR_BACKEND, and ECR_FRONTEND must be set in your environment."
  exit 1
fi

GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "🔐 Logging into Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "🏗️ Building production Docker images..."
docker build -f backend/Dockerfile.prod -t $ECR_BACKEND:latest -t $ECR_BACKEND:$GIT_SHA ./backend
docker build -f frontend/Dockerfile.prod -t $ECR_FRONTEND:latest -t $ECR_FRONTEND:$GIT_SHA ./frontend

echo "📤 Pushing backend images to ECR..."
docker push $ECR_BACKEND:latest
docker push $ECR_BACKEND:$GIT_SHA

echo "📤 Pushing frontend images to ECR..."
docker push $ECR_FRONTEND:latest
docker push $ECR_FRONTEND:$GIT_SHA

echo "🚀 Updating ECS Fargate services (force-new-deployment)..."
aws ecs update-service --cluster sapflow-cluster --service sapflow-backend --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster sapflow-cluster --service sapflow-frontend --force-new-deployment --region $AWS_REGION

echo "⏳ Waiting for ECS Fargate services to stabilize..."
aws ecs wait services-stable --cluster sapflow-cluster --services sapflow-backend sapflow-frontend --region $AWS_REGION

echo "🔍 Fetching load balancer URL from Terraform..."
ALB_URL=$(cd infra/terraform && terraform output -raw alb_dns_name 2>/dev/null || echo "Unknown ALB URL")

echo ""
echo "==============================================="
echo "✅ SAPFlow deployed successfully!"
echo "Dashboard: http://$ALB_URL"
echo "API Docs:  http://$ALB_URL/docs"
echo "==============================================="

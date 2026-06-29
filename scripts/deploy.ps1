# Ensure variables are set
if ($null -eq $env:AWS_REGION -or $null -eq $env:AWS_ACCOUNT_ID -or $null -eq $env:ECR_BACKEND -or $null -eq $env:ECR_FRONTEND) {
    Write-Error "AWS_REGION, AWS_ACCOUNT_ID, ECR_BACKEND, and ECR_FRONTEND must be set in your environment."
    exit 1
}

$GitSha = (git rev-parse --short HEAD 2>$null)
if ($null -eq $GitSha) { $GitSha = "latest" }

Write-Host "🔐 Logging into Amazon ECR..."
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$($env:AWS_ACCOUNT_ID).dkr.ecr.$($env:AWS_REGION).amazonaws.com"

Write-Host "🏗️ Building production Docker images..."
docker build -f backend/Dockerfile.prod -t "$($env:ECR_BACKEND):latest" -t "$($env:ECR_BACKEND):$GitSha" ./backend
docker build -f frontend/Dockerfile.prod -t "$($env:ECR_FRONTEND):latest" -t "$($env:ECR_FRONTEND):$GitSha" ./frontend

Write-Host "📤 Pushing backend images to ECR..."
docker push "$($env:ECR_BACKEND):latest"
docker push "$($env:ECR_BACKEND):$GitSha"

Write-Host "📤 Pushing frontend images to ECR..."
docker push "$($env:ECR_FRONTEND):latest"
docker push "$($env:ECR_FRONTEND):$GitSha"

Write-Host "🚀 Updating ECS Fargate services..."
aws ecs update-service --cluster sapflow-cluster --service sapflow-backend --force-new-deployment --region $env:AWS_REGION
aws ecs update-service --cluster sapflow-cluster --service sapflow-frontend --force-new-deployment --region $env:AWS_REGION

Write-Host "⏳ Waiting for ECS Fargate services to stabilize..."
aws ecs wait services-stable --cluster sapflow-cluster --services sapflow-backend sapflow-frontend --region $env:AWS_REGION

Write-Host "🔍 Fetching load balancer URL from Terraform..."
Push-Location infra/terraform
$AlbUrl = (terraform output -raw alb_dns_name 2>$null)
if ($null -eq $AlbUrl) { $AlbUrl = "Unknown ALB URL" }
Pop-Location

Write-Host ""
Write-Host "==============================================="
Write-Host "✅ SAPFlow deployed successfully!"
Write-Host "Dashboard: http://$AlbUrl"
Write-Host "API Docs:  http://$AlbUrl/docs"
Write-Host "==============================================="

# SAPFlow — SAP Transport Management CI/CD DevOps Pipeline

A production-grade automated CI/CD DevOps pipeline for SAP S/4HANA transport management, deployed on AWS with a real-time monitoring dashboard.

## 🚀 Live Demo

| Service | URL |
|---------|-----|
| Dashboard | http://${ALB_DNS_NAME} *(Replaced with ALB DNS once provisioned)* |
| API Docs | http://${ALB_DNS_NAME}/docs |
| GitHub Actions | https://github.com/Rajiv6165/sapflow/actions |

---

## Architecture

```
                       Internet
                          │
                          ▼
             Application Load Balancer (ALB)
             ├── /api/*  ──▶ ECS Fargate (sapflow-backend, port 8000)
             ├── /ws     ──▶ ECS Fargate (sapflow-backend, port 8000)
             └── /*      ──▶ ECS Fargate (sapflow-frontend, port 3000)
             
ECS Fargate Services (Private Subnets):
  ├── sapflow-backend   (FastAPI + uvicorn, port 8000)
  └── sapflow-frontend  (Next.js, port 3000)

Supporting Services:
  ├── RDS PostgreSQL    (db.t3.micro, sapflow database)
  ├── ElastiCache Redis (cache.t3.micro, Redis 7.0 cache)
  ├── ECR               (Docker image registry)
  ├── CloudWatch        (logs + metric alarms)
  ├── SNS               (email alerts)
  └── Secrets Manager   (secure env var injection)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, AsyncPG, Redis |
| **Database** | PostgreSQL 15 (AWS RDS) |
| **Cache** | Redis 7 (AWS ElastiCache) |
| **Container** | Docker, AWS ECS Fargate |
| **Registry** | AWS ECR |
| **CI/CD** | GitHub Actions |
| **Monitoring** | AWS CloudWatch, SNS |
| **SAP Integration** | SAP BTP APIs, ABAP Code Inspector |
| **Infrastructure** | Terraform |

---

## Features

- **Automated Transport Promotion**: Promote SAP transports between DEV, QA, and PROD systems.
- **ABAP Code Inspection**: Validate ABAP code quality before transport promotion (using mock mode or BTP connections).
- **Real-time Monitoring**: WebSocket-based dashboard for pipeline status, system health snapshots, and live alerts.
- **AWS Production Infrastructure**: Provisions secure VPC, RDS, Redis, Application Load Balancers, task execution IAM roles, and secret injection.
- **Robust Database Migrations**: Schema updates are managed via Alembic migrations instead of standard SQL executions.

---

## Prerequisites

- Docker and Docker Compose
- Terraform >= 1.0
- Python 3.11+
- Node.js 18+
- AWS CLI configured with admin permissions

---

## Development Setup

### 1. Clone and Setup Environment
```bash
git clone https://github.com/Rajiv6165/sapflow.git
cd sapflow
cp .env.example .env
```

### 2. Run Local Containers (FastAPI + Next.js + Postgres + Redis)
```bash
docker-compose up --build -d
```
Access the local dashboard at http://localhost:3000 and the API documentation at http://localhost:8000/docs.

### 3. Run Database Migrations Locally
```bash
cd backend
alembic upgrade head
```

---

## Production Deployment to AWS

### 1. Initialize AWS Infrastructure
Navigate to the Terraform folder, configure S3 backend manually, and run:
```bash
cd infra/terraform
terraform init
terraform plan -var="db_password=YourSecurePass123" \
               -var="alert_email=rajivthakkar6165@gmail.com" \
               -var="github_token=ghp_xxx" \
               -var="github_webhook_secret=sapflow-secret" \
               -var="backend_image=placeholder" \
               -var="frontend_image=placeholder"
```
Apply the configuration:
```bash
terraform apply -var="db_password=YourSecurePass123" \
                -var="alert_email=rajivthakkar6165@gmail.com" \
                -var="github_token=ghp_xxx" \
                -var="github_webhook_secret=sapflow-secret" \
                -var="backend_image=$(terraform output -raw ecr_backend_url):latest" \
                -var="frontend_image=$(terraform output -raw ecr_frontend_url):latest"
```

### 2. Build & Deploy Containers
Set ECR credentials and invoke the deploy script:
```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=ap-south-1
export ECR_BACKEND=$(cd infra/terraform && terraform output -raw ecr_backend_url)
export ECR_FRONTEND=$(cd infra/terraform && terraform output -raw ecr_frontend_url)

chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

---

## Troubleshooting

- **Check ECS Container Logs**: Logs are piped directly to CloudWatch under `/sapflow/backend` and `/sapflow/frontend` groups.
- **Teardown**: To destroy all AWS resources and avoid recurring costs, run:
  ```bash
  chmod +x scripts/destroy.sh
  ./scripts/destroy.sh
  ```

## License
MIT

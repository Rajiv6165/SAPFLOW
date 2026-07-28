# SAPFlow

> Enterprise-grade SAP DevOps automation pipeline — CI/CD for SAP S/4HANA 
> transport management with real-time monitoring, built on FastAPI, React, 
> Docker, AWS, and SAP BTP.

[![CI](https://github.com/Rajiv6165/sapflow/actions/workflows/ci.yml/badge.svg)](https://github.com/Rajiv6165/sapflow/actions/workflows/ci.yml) [![Deploy](https://github.com/Rajiv6165/sapflow/actions/workflows/deploy.yml/badge.svg)](https://github.com/Rajiv6165/sapflow/actions/workflows/deploy.yml)

## 🚀 Live Demo

> Deploy with `terraform apply` to get your own live URL.
> See [Deployment Guide](#deployment) below.

| Endpoint | Description |
|----------|-------------|
| `/` | Real-time monitoring dashboard |
| `/docs` | Interactive FastAPI documentation |
| `/health` | System health check |
| `/webhooks/github` | GitHub Actions webhook receiver |

## 📐 Architecture

```
[ Developer Push ] ──▶ [ GitHub Actions CI/CD ] ──▶ [ Docker Container Builds ]
                                                             │
                                                             ▼
[ Web Browser Dashboard ] ◀── [ AWS ECS Fargate ] ◀── [ AWS ALB Routing ]
         │
         ▼
[ Real/Mock SAP BTP API ] ◀── [ ABAP Code Inspector & Transport Promoter ]
```

## ✨ Key Features
- Automated CI/CD pipeline for SAP transport validation
- Real-time WebSocket dashboard with live pipeline tracking  
- ABAP Code Inspector integration via SAP BTP
- One-click transport promotion (DEV → QA → PROD)
- AWS CloudWatch monitoring with SNS alerting
- Infrastructure as Code with Terraform
- Dual-mode SAP integration: works fully offline in mock mode, 
  switches to live SAP BTP automatically when credentials are added

## 🛠 Tech Stack

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

## 🚢 Deployment

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform >= 1.0 installed
- Docker Desktop running

### Deploy to AWS
```bash
# 1. Initialize Terraform
cd infra/terraform
terraform init

# 2. Plan infrastructure (~35 AWS resources)
terraform plan -var="db_password=YourPass" -var="alert_email=you@email.com" ...

# 3. Apply (creates VPC, ECS, RDS, ALB, CloudWatch, SNS)
terraform apply

# 4. Build and push Docker images + deploy to ECS
cd ../..
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 5. Open your live dashboard
echo "Dashboard: http://$(cd infra/terraform && terraform output -raw alb_dns_name)"
```

### Tear Down (stop AWS charges)
```bash
chmod +x scripts/destroy.sh
./scripts/destroy.sh
```

## 🏃 Quick Start

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

### 4. Makefile Commands
Shortcut commands for local development using `make`:

| Command | Description |
|---|---|
| `make up` | Start local containers in detached mode (`docker-compose up --build -d`) |
| `make down` | Stop local containers (`docker-compose down`) |
| `make test` | Run backend pytest suite inside the backend container |
| `make seed` | Run seed script to populate DB with sample transports and pipeline runs |
| `make logs` | Tail logs of running containers (`docker-compose logs -f`) |


## 🔌 SAP BTP Integration
This project works in two modes:
- **Mock mode** (default): No SAP account needed. Realistic simulated 
  SAP data for full local development and demo.
- **Live mode**: Connect a real SAP BTP trial account by adding credentials 
  to `.env`. The system detects valid credentials automatically and switches 
  modes with zero code changes — see the connection status badge on the dashboard.

## 📊 What This Project Demonstrates
- End-to-end DevOps pipeline design for enterprise SAP systems
- Cloud-native architecture (ECS Fargate, RDS, ElastiCache, ALB)
- Infrastructure as Code (Terraform)
- Real-time systems (WebSocket, event-driven architecture)
- Graceful degradation and fault-tolerant API integration design
- Production-grade CI/CD with GitHub Actions

## 🤝 Contributing

This is a portfolio project but PRs are welcome. 
Open an issue first to discuss what you'd like to change.

## 📷 Screenshots
[Add dashboard screenshots here]

## 🧑💻 Author
Rajiv N Thakker — [LinkedIn](https://www.linkedin.com/in/rajiv-thakker/) — [GitHub](https://github.com/Rajiv6165)

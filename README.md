<<<<<<< HEAD
# SAPFlow - SAP Transport Management CI/CD Pipeline

A production-grade automated CI/CD DevOps pipeline for SAP S/4HANA transport management, deployed on AWS with real-time monitoring dashboard.

## Features

- **Automated Transport Promotion**: Promote SAP transports between DEV, QA, and PROD systems
- **ABAP Code Inspection**: Validate ABAP code quality before transport promotion
- **Real-time Monitoring**: WebSocket-based dashboard for pipeline status, system health, and alerts
- **AWS Integration**: CloudWatch metrics, SNS alerts, and ECS deployment
- **GitHub Actions**: CI/CD workflows for automated testing and deployment
- **SAP BTP Integration**: OAuth2 authentication with SAP Business Technology Platform
- **Mock Mode**: Offline development mode without SAP system connectivity

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend      │────▶│   Backend    │────▶│   SAP BTP   │
│  (Next.js)      │     │  (FastAPI)   │     │   System    │
└─────────────────┘     └──────────────┘     └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │    Redis     │
                        └──────────────┘
```

## Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, AsyncPG, Redis
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container**: Docker, Docker Compose
- **AWS**: ECS, CloudWatch, SNS, ECR
- **CI/CD**: GitHub Actions
- **SAP Integration**: SAP BTP OAuth2

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- AWS Account (for production deployment)
- SAP BTP credentials (for production)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd SAPFLOW
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your configuration:

```env
# SAP BTP Configuration
SAP_BTP_HOST=https://your-sap-btp-host.com
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret
SAP_TOKEN_URL=https://your-sap-btp-host.com/oauth/token
SAP_MOCK_MODE=true

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
AWS_ECR_REGISTRY=your_account_id.dkr.ecr.ap-south-1.amazonaws.com
SNS_ALERT_TOPIC_arn=arn:aws:sns:...

# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_REPO=owner/repo

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/sapflow
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/pipeline
```

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend dashboard on port 3000
- Transport runner service

### 4. Access the Dashboard

Open http://localhost:3000 in your browser.

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Transport Runner

```bash
cd transport-runner
pip install -r requirements.txt
python test_runner.py --transport-id DEVK900001 --source-system DEV --mock
```

## Production Deployment

### 1. Build and Push Docker Images

```bash
# Build backend
docker build -t sapflow-backend ./backend
docker tag sapflow-backend:latest <ECR_REGISTRY>/sapflow-backend:latest
docker push <ECR_REGISTRY>/sapflow-backend:latest

# Build frontend
docker build -t sapflow-frontend ./frontend
docker tag sapflow-frontend:latest <ECR_REGISTRY>/sapflow-frontend:latest
docker push <ECR_REGISTRY>/sapflow-frontend:latest

# Build transport-runner
docker build -t sapflow-transport-runner ./transport-runner
docker tag sapflow-transport-runner:latest <ECR_REGISTRY>/sapflow-transport-runner:latest
docker push <ECR_REGISTRY>/sapflow-transport-runner:latest
```

### 2. Deploy to ECS

```bash
aws ecs register-task-definition --cli-input-json file://infra/ecs-task-definition.json
aws ecs update-service --cluster sapflow --service sapflow-backend --task-definition sapflow-backend
```

### 3. Setup CloudWatch Alarms

```bash
aws cloudwatch put-metric-alarm --cli-input-json file://infra/cloudwatch-alarms.json
```

### 4. Setup SNS Topic

```bash
python infra/sns-setup.py
```

### 5. Start Production Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API Endpoints

### Pipeline
- `GET /pipeline/status` - Get current pipeline status
- `GET /pipeline/runs/{run_id}` - Get specific run details
- `POST /pipeline/trigger?branch={branch}` - Trigger pipeline
- `GET /pipeline/metrics` - Get pipeline metrics

### Transport
- `GET /transport/active` - Get active transports
- `GET /transport/history` - Get transport history
- `POST /transport/promote` - Promote transport
- `GET /transport/{transport_id}` - Get transport details
- `POST /transport/validate?transport_id={id}` - Validate transport

### Health
- `GET /health/system` - Get SAP system health
- `GET /health/history?limit={n}` - Get health history

### WebSocket
- `WS /ws/pipeline` - Real-time pipeline status updates

## GitHub Actions Workflows

### CI Pipeline (`.github/workflows/ci.yml`)

Triggers on push to main/develop:
1. Code quality checks (flake8, black)
2. Unit tests with coverage
3. ABAP validation (mock mode)
4. Docker build and push to ECR
5. Slack notification

### Transport Promotion (`.github/workflows/transport-promote.yml`)

Manual workflow to promote transports:
1. Select source system (DEV/QA)
2. Enter transport ID
3. Select target system (QA/PROD)
4. Call FastAPI promote endpoint

## Monitoring

### CloudWatch Metrics

- CPU Utilization (ECS)
- Memory Utilization (ECS)
- Pipeline Success Rate (Custom)
- Transport Validation Failures (Custom)

### SNS Alerts

- Pipeline failures
- High CPU/memory usage
- Transport validation failures
- System health degradation

## Troubleshooting

### Backend won't start

Check database connection:
```bash
docker-compose logs postgres
docker-compose logs backend
```

### Frontend can't connect to backend

Verify CORS settings in `backend/core/config.py` and environment variables.

### SAP BTP connection fails

Enable mock mode in `.env`:
```env
SAP_MOCK_MODE=true
```

### Transport validation fails

Check transport-runner logs:
```bash
docker-compose logs transport-runner
```

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
=======
# SAPFLOW
Enterprise-grade SAP DevOps automation pipeline — CI/CD for SAP S/4HANA transport management with real-time monitoring dashboard, built on FastAPI · React · Docker · AWS · SAP BTP
>>>>>>> 5e1a51ffb743a9739f7fce1010120d5108924ccd

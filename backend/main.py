from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.models.database import Base, PipelineRun, SystemHealthSnapshot
from backend.core.config import settings
from backend.core.websocket_manager import manager
from backend.routers import pipeline, transport, health, webhooks
from backend.services.sap_btp import SAPBTPService
from backend.services.aws_alerts import AWSAlertsService
from backend.services.github_service import GitHubService
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAPFlow API", version="1.0.0")

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {duration:.4f}s"
    )
    return response

if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router)
app.include_router(transport.router)
app.include_router(health.router)
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

sap_service = SAPBTPService()
aws_service = AWSAlertsService()


@app.on_event("startup")
async def startup_event():
    if settings.is_production and settings.SAP_MOCK_MODE:
        logger.warning("⚠️ SAP MOCK MODE is ENABLED in production environment!")

    if not settings.is_production:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        engine = create_async_engine(db_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        await engine.dispose()
    
    app.state.github = GitHubService()
    
    asyncio.create_task(poll_system_health())
    asyncio.create_task(broadcast_pipeline_status())
    asyncio.create_task(sync_pipeline_from_github())


async def poll_system_health():
    while True:
        try:
            health_data = await sap_service.get_system_health()
            
            db_url = settings.DATABASE_URL
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                
            engine = create_async_engine(db_url, echo=False)
            async with AsyncSession(engine) as session:
                snapshot = SystemHealthSnapshot(
                    cpu_percent=health_data["cpu_percent"],
                    memory_percent=health_data["memory_percent"],
                    active_users=health_data["active_users"],
                    avg_response_ms=health_data["avg_response_ms"],
                    status=health_data["status"]
                )
                session.add(snapshot)
                await session.commit()
            await engine.dispose()
            logger.info("System health snapshot recorded")
        except Exception as e:
            logger.error(f"Error polling system health: {e}")
        
        await asyncio.sleep(60)


async def broadcast_pipeline_status():
    while True:
        try:
            await manager.broadcast()
        except Exception as e:
            logger.error(f"Error broadcasting pipeline status: {e}")
        
        await asyncio.sleep(5)


async def sync_pipeline_from_github():
    while True:
        try:
            db_url = settings.DATABASE_URL
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                
            engine = create_async_engine(db_url, echo=False)
            async with AsyncSession(engine) as session:
                github_service = getattr(app.state, "github", None)
                if github_service:
                    synced = await github_service.sync_runs_to_db(session)
                    if synced > 0:
                        logger.info(f"Synced {synced} pipeline runs from GitHub. Broadcasting update.")
                        await manager.broadcast()
            await engine.dispose()
        except Exception as e:
            logger.warning(f"Error syncing pipeline from GitHub: {e}")
            
        await asyncio.sleep(settings.PIPELINE_SYNC_INTERVAL)


@app.websocket("/ws/pipeline")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"message": "SAPFlow API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

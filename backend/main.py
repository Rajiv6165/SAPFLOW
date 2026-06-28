from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.models.database import Base, PipelineRun, SystemHealthSnapshot
from backend.core.config import settings
from backend.core.websocket_manager import manager
from backend.routers import pipeline, transport, health
from backend.services.sap_btp import SAPBTPService
from backend.services.aws_alerts import AWSAlertsService
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAPFlow API", version="1.0.0")

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

sap_service = SAPBTPService()
aws_service = AWSAlertsService()


@app.on_event("startup")
async def startup_event():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    await engine.dispose()
    
    asyncio.create_task(poll_system_health())
    asyncio.create_task(broadcast_pipeline_status())


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

from fastapi import WebSocket
from typing import List
import json
import logging
from datetime import datetime, time
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.core.config import settings
from backend.models.database import PipelineRun, TransportRecord, SystemHealthSnapshot

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict = None):
        if not self.active_connections:
            return
        
        if message is None:
            try:
                db_url = settings.DATABASE_URL
                if db_url.startswith("postgresql://"):
                    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                
                engine = create_async_engine(db_url, echo=False)
                async with AsyncSession(engine) as session:
                    now = datetime.utcnow()
                    today_start = datetime.combine(now.date(), time.min)
                    
                    # 1. Total runs today
                    today_runs_q = await session.execute(
                        select(PipelineRun).where(PipelineRun.triggered_at >= today_start)
                    )
                    today_runs = today_runs_q.scalars().all()
                    total_runs_today = len(today_runs)
                    
                    # 2. Success rate
                    success_runs = [r for r in today_runs if r.status == "success"]
                    success_rate = (len(success_runs) / total_runs_today * 100.0) if total_runs_today > 0 else 0.0
                    success_rate = round(success_rate, 1)
                    
                    # 3. Recent runs (last 10)
                    recent_runs_q = await session.execute(
                        select(PipelineRun)
                        .order_by(PipelineRun.triggered_at.desc())
                        .limit(10)
                    )
                    recent_runs = recent_runs_q.scalars().all()
                    
                    # 4. Active transports
                    active_transports_q = await session.execute(
                        select(func.count(TransportRecord.id))
                        .where(TransportRecord.status.in_(["in_progress", "pending"]))
                    )
                    active_transports = active_transports_q.scalar() or 0
                    
                    # 5. System status
                    latest_health_q = await session.execute(
                        select(SystemHealthSnapshot)
                        .order_by(SystemHealthSnapshot.recorded_at.desc())
                        .limit(1)
                    )
                    latest_health = latest_health_q.scalar_one_or_none()
                    system_status = latest_health.status if latest_health else "unknown"
                    
                    message = {
                        "type": "pipeline_update",
                        "timestamp": now.isoformat(),
                        "summary": {
                            "total_runs_today": total_runs_today,
                            "success_rate": success_rate,
                            "active_transports": active_transports,
                            "system_status": system_status
                        },
                        "recent_runs": [
                            {
                                "id": str(run.id),
                                "run_id": run.run_id,
                                "branch": run.branch,
                                "commit_sha": run.commit_sha,
                                "status": run.status,
                                "duration_seconds": run.duration_seconds,
                                "triggered_at": run.triggered_at.isoformat()
                            }
                            for run in recent_runs
                        ]
                    }
                await engine.dispose()
            except Exception as e:
                logger.error(f"Error querying database for WebSocket broadcast: {e}")
                return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()

from fastapi import APIRouter, HTTPException
from backend.seed import seed_database
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.models.database import PipelineRun, TransportRecord, SystemHealthSnapshot, engine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

# Initialize last reset time
LAST_RESET_TIME = datetime.utcnow().isoformat()


@router.post("/reset")
async def reset_demo():
    """Reset and seed demo database. No params. Writes seed data to DB, broadcasts WS. Returns success status."""
    global LAST_RESET_TIME
    try:
        logger.info("Initiating demo data reset...")
        await seed_database()
        LAST_RESET_TIME = datetime.utcnow().isoformat()
        
        # Broadcast demo reset via WebSocket manager
        try:
            from backend.core.websocket_manager import manager
            manager.add_event(
                event_type="DEMO_RESET",
                message="Demo database has been successfully reset and seeded."
            )
            await manager.broadcast()
        except Exception as ws_err:
            logger.warning(f"Failed to broadcast demo reset event: {ws_err}")
            
        return {"status": "success", "message": "Demo database successfully reset and seeded"}
    except Exception as e:
        logger.error(f"Error resetting demo database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_demo_status():
    """Get demo database status. No params. Returns counts of runs, transports, snapshots, and last reset time. No side effects."""
    try:
        async with AsyncSession(engine) as session:
            runs_q = await session.execute(select(func.count(PipelineRun.id)))
            transports_q = await session.execute(select(func.count(TransportRecord.id)))
            snapshots_q = await session.execute(select(func.count(SystemHealthSnapshot.id)))
            
            runs_count = runs_q.scalar() or 0
            transports_count = transports_q.scalar() or 0
            snapshots_count = snapshots_q.scalar() or 0
            
        return {
            "pipeline_runs": runs_count,
            "transport_records": transports_count,
            "health_snapshots": snapshots_count,
            "last_reset": LAST_RESET_TIME
        }
    except Exception as e:
        logger.error(f"Error fetching demo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

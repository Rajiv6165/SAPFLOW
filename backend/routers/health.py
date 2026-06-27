from fastapi import APIRouter, HTTPException
from backend.services.sap_btp import SAPBTPService
from backend.models.database import SystemHealthSnapshot
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])
sap_service = SAPBTPService()


@router.get("/system")
async def get_system_health():
    try:
        health_data = await sap_service.get_system_health()
        return health_data
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_health_history(limit: int = 50):
    from sqlalchemy import select
    from backend.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from backend.models.database import SystemHealthSnapshot, Base
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(
                select(SystemHealthSnapshot)
                .order_by(SystemHealthSnapshot.recorded_at.desc())
                .limit(limit)
            )
            snapshots = result.scalars().all()
            return [
                {
                    "recorded_at": snapshot.recorded_at.isoformat(),
                    "cpu_percent": snapshot.cpu_percent,
                    "memory_percent": snapshot.memory_percent,
                    "active_users": snapshot.active_users,
                    "avg_response_ms": snapshot.avg_response_ms,
                    "status": snapshot.status
                }
                for snapshot in snapshots
            ]
        except Exception as e:
            logger.error(f"Error fetching health history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

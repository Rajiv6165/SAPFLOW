from fastapi import APIRouter, HTTPException
from backend.services.sap_btp import SAPBTPService
from backend.models.database import SystemHealthSnapshot, engine
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])
sap_service = SAPBTPService()


@router.get("")
@router.get("/")
async def root_health():
    """Health check endpoint. Returns service status. No params. Returns status object."""
    return {"status": "ok", "service": "sapflow-backend"}


@router.get("/sap-connection")
async def get_sap_connection():
    """Get SAP BTP connection status. No params. Returns connection status with timestamp."""
    try:
        status = sap_service.get_connection_status()
        status["last_checked"] = datetime.utcnow().isoformat()
        return status
    except Exception as e:
        logger.error(f"Error fetching SAP connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sap-connection/test")
async def test_sap_connection():
    """Test SAP BTP connection. No params. Returns test result. No side effects."""
    try:
        result = await sap_service.test_connection()
        return result
    except Exception as e:
        logger.error(f"Error testing SAP connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def get_system_health():
    """Get SAP system health metrics. No params. Returns CPU, memory, users, response time. No side effects."""
    try:
        health_data = await sap_service.get_system_health()
        return health_data
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_health_history(limit: int = 48):
    """Get health history from DB. Query param: limit (default 48). Returns list of snapshots. No side effects."""
    from sqlalchemy import select

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
                    "status": snapshot.status,
                }
                for snapshot in snapshots
            ]
        except Exception as e:
            logger.error(f"Error fetching health history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

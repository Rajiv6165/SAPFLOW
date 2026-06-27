from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.database import TransportRecord
from backend.services.sap_btp import SAPBTPService
from backend.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transport", tags=["transport"])
sap_service = SAPBTPService()


async def get_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        yield session


@router.get("/active")
async def get_active_transports():
    try:
        transports = await sap_service.get_active_transports()
        return {"transports": transports}
    except Exception as e:
        logger.error(f"Error fetching active transports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_transport_history(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(TransportRecord)
            .order_by(TransportRecord.promoted_at.desc())
            .limit(50)
        )
        records = result.scalars().all()
        
        return {
            "transports": [
                {
                    "id": str(record.id),
                    "transport_id": record.transport_id,
                    "description": record.description,
                    "source_system": record.source_system,
                    "target_system": record.target_system,
                    "status": record.status,
                    "promoted_by": record.promoted_by,
                    "promoted_at": record.promoted_at.isoformat(),
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                    "validation_report": record.validation_report
                }
                for record in records
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching transport history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote")
async def promote_transport(
    transport_id: str,
    source_system: str,
    target_system: str,
    promoted_by: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await sap_service.promote_transport(transport_id, source_system, target_system)
        
        new_record = TransportRecord(
            transport_id=transport_id,
            description=f"Transport {transport_id}",
            source_system=source_system,
            target_system=target_system,
            status=result.get("status", "pending"),
            promoted_by=promoted_by,
            promoted_at=datetime.utcnow(),
            validation_report=result
        )
        
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        
        return {
            "id": str(new_record.id),
            "transport_id": new_record.transport_id,
            "status": new_record.status,
            "message": result.get("message", "Transport promotion initiated")
        }
    except Exception as e:
        logger.error(f"Error promoting transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transport_id}")
async def get_transport_details(transport_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(TransportRecord).where(TransportRecord.transport_id == transport_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="Transport not found")
        
        return {
            "id": str(record.id),
            "transport_id": record.transport_id,
            "description": record.description,
            "source_system": record.source_system,
            "target_system": record.target_system,
            "status": record.status,
            "promoted_by": record.promoted_by,
            "promoted_at": record.promoted_at.isoformat(),
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "validation_report": record.validation_report
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transport details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_transport(transport_id: str):
    try:
        from transport_runner.abap_inspector import ABAPInspector
        from transport_runner.transport_validator import TransportValidator
        
        inspector = ABAPInspector(
            sap_host=settings.SAP_BTP_HOST,
            client_id=settings.SAP_CLIENT_ID,
            client_secret=settings.SAP_CLIENT_SECRET
        )
        
        inspection_result = inspector.run_code_inspection(transport_id)
        objects = inspector.validate_transport_objects(transport_id)
        
        validator = TransportValidator(objects)
        validation_result = validator.generate_report()
        
        return {
            "transport_id": transport_id,
            "inspection": inspection_result,
            "validation": validation_result,
            "overall_valid": validation_result.get("is_valid", False)
        }
    except Exception as e:
        logger.error(f"Error validating transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))

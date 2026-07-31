from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, or_
from backend.models.database import TransportRecord, engine
from backend.services.sap_btp import SAPBTPService
from backend.core.config import settings
from backend.models.schemas import TransportPromoteRequest
from backend.core.limiter import limiter
from datetime import datetime
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transport", tags=["transport"])
sap_service = SAPBTPService()


async def get_db():
    async with AsyncSession(engine) as session:
        yield session


@router.get("/active")
async def get_active_transports():
    """Get active transports from SAP BTP. No params. Returns list of active transports. No side effects."""
    try:
        transports = await sap_service.get_active_transports()
        return {"transports": transports}
    except Exception as e:
        logger.error(f"Error fetching active transports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_transport_stats(db: AsyncSession = Depends(get_db)):
    """Get transport statistics grouped by landscape (FINANCE, LOGISTICS, DEFAULT)."""
    try:
        # Aggregate query using SQLAlchemy functions
        stats_query = select(
            TransportRecord.landscape,
            func.count(TransportRecord.id).label("total_transports"),
            func.sum(case((TransportRecord.status == "success", 1), else_=0)).label(
                "success_count"
            ),
            func.sum(
                case(
                    (
                        or_(
                            TransportRecord.transport_id.like("%_ROLLBACK%"),
                            TransportRecord.promoted_by == "rollback",
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("rollbacks_count"),
        ).group_by(TransportRecord.landscape)

        stats_res = await db.execute(stats_query)
        stats_rows = stats_res.all()

        # Query completed records for average duration calculation
        durations_query = select(
            TransportRecord.landscape,
            TransportRecord.promoted_at,
            TransportRecord.completed_at,
        ).where(TransportRecord.completed_at.isnot(None))

        durations_res = await db.execute(durations_query)
        duration_rows = durations_res.all()

        landscape_durations = {}
        for row in duration_rows:
            ls = row.landscape or "DEFAULT"
            if row.promoted_at and row.completed_at:
                dur_sec = (row.completed_at - row.promoted_at).total_seconds()
                if dur_sec >= 0:
                    landscape_durations.setdefault(ls, []).append(dur_sec)

        known_landscapes = ["DEFAULT", "FINANCE", "LOGISTICS"]
        landscape_map = {}
        for ls in known_landscapes:
            landscape_map[ls] = {
                "landscape": ls,
                "total_transports": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "rollbacks_count": 0,
            }

        for row in stats_rows:
            ls = row.landscape or "DEFAULT"
            total = row.total_transports or 0
            successes = row.success_count or 0
            rollbacks = row.rollbacks_count or 0

            dur_list = landscape_durations.get(ls, [])
            avg_dur = round(sum(dur_list) / len(dur_list), 2) if dur_list else 0.0
            success_rate = round((successes / total) * 100, 2) if total > 0 else 0.0

            landscape_map[ls] = {
                "landscape": ls,
                "total_transports": total,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_dur,
                "rollbacks_count": rollbacks,
            }

        stats_list = list(landscape_map.values())

        return {"stats": stats_list, "by_landscape": landscape_map}
    except Exception as e:
        logger.error(f"Error fetching transport stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/landscapes")
async def get_landscapes(db: AsyncSession = Depends(get_db)):
    """Get available transport landscapes. No params. Returns list of landscape names from DB. No side effects."""
    try:
        result = await db.execute(select(TransportRecord.landscape).distinct())
        landscapes = result.scalars().all()
        landscapes_list = [l for l in landscapes if l]
        if "DEFAULT" not in landscapes_list:
            landscapes_list.insert(0, "DEFAULT")
        return sorted(list(set(landscapes_list)))
    except Exception as e:
        logger.error(f"Error fetching landscapes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_transport_history(
    landscape: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get transport history from DB with pagination. Query params: landscape, page (default 1), limit (default 20, max 100)."""
    try:
        page = max(1, page)
        limit = min(100, max(1, limit))

        query = select(TransportRecord)
        count_query = select(func.count(TransportRecord.id))

        if landscape and landscape != "all" and landscape.strip() != "":
            query = query.where(TransportRecord.landscape == landscape)
            count_query = count_query.where(TransportRecord.landscape == landscape)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one() or 0

        total_pages = math.ceil(total / limit) if total > 0 else 0
        offset = (page - 1) * limit

        result = await db.execute(
            query.order_by(TransportRecord.promoted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        records = result.scalars().all()

        items = [
            {
                "id": str(record.id),
                "transport_id": record.transport_id,
                "description": record.description,
                "source_system": record.source_system,
                "target_system": record.target_system,
                "status": record.status,
                "promoted_by": record.promoted_by,
                "promoted_at": record.promoted_at.isoformat(),
                "completed_at": record.completed_at.isoformat()
                if record.completed_at
                else None,
                "validation_report": record.validation_report,
                "landscape": record.landscape,
            }
            for record in records
        ]

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        }
    except Exception as e:
        logger.error(f"Error fetching transport history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote")
@limiter.limit("10/minute")
async def promote_transport(
    request: Request,
    promote_req: TransportPromoteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Promote transport between systems. Body: transport_id, source, target, landscape. Writes to DB, broadcasts WS, sends Slack."""
    try:
        transport_id = promote_req.transport_id
        source_system = promote_req.source_system
        target_system = promote_req.target_system
        promoted_by = promote_req.promoted_by
        landscape = promote_req.landscape or "DEFAULT"

        # Check if record already exists and is already promoted
        existing_record_q = await db.execute(
            select(TransportRecord).where(TransportRecord.transport_id == transport_id)
        )
        existing_record = existing_record_q.scalar_one_or_none()

        if (
            existing_record
            and existing_record.status == "success"
            and existing_record.target_system == target_system
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Transport {transport_id} is already promoted to {target_system}",
            )

        result = await sap_service.promote_transport(
            transport_id, source_system, target_system
        )

        if existing_record:
            existing_record.source_system = source_system
            existing_record.target_system = target_system
            existing_record.status = result.get("status", "pending")
            existing_record.promoted_by = promoted_by
            existing_record.promoted_at = datetime.utcnow()
            existing_record.validation_report = result
            existing_record.landscape = landscape
            await db.commit()
            await db.refresh(existing_record)

            record = existing_record
        else:
            record = TransportRecord(
                transport_id=transport_id,
                description=f"Transport {transport_id}",
                source_system=source_system,
                target_system=target_system,
                status=result.get("status", "pending"),
                promoted_by=promoted_by,
                promoted_at=datetime.utcnow(),
                validation_report=result,
                landscape=landscape,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)

        if record.status == "success":
            from backend.core.websocket_manager import manager

            manager.add_event(
                event_type="TRANSPORT_PROMOTED",
                message=f"Transport {transport_id} promoted to {target_system}",
                transport_id=transport_id,
            )
            await manager.broadcast()

            # Send Slack notification
            try:
                await request.app.state.slack.notify_transport_promoted(
                    transport_id=transport_id,
                    source=source_system,
                    target=target_system,
                    promoted_by=promoted_by,
                )
            except Exception as slack_err:
                logger.error(
                    f"Error sending Slack notification for promotion: {slack_err}"
                )

        return {
            "id": str(record.id),
            "transport_id": record.transport_id,
            "status": record.status,
            "message": result.get("message", "Transport promotion updated/initiated"),
            "landscape": record.landscape,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{transport_id}/rollback")
@limiter.limit("10/minute")
async def rollback_transport(
    request: Request, transport_id: str, db: AsyncSession = Depends(get_db)
):
    """Rollback transport to previous system. Path param: transport_id. Writes rollback record, broadcasts WS, sends Slack."""
    try:
        # Find original transport record
        result = await db.execute(
            select(TransportRecord).where(TransportRecord.transport_id == transport_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Transport not found")

        if record.status != "success":
            raise HTTPException(
                status_code=400, detail="Can only rollback successful transports"
            )

        current_target = record.target_system
        current_source = record.source_system
        landscape = record.landscape

        # Execute SAP BTP rollback
        await sap_service.rollback_transport(transport_id, current_target)

        # New rollback record ID
        rollback_id = f"{transport_id}_ROLLBACK"

        # Check if rollback record already exists
        existing_q = await db.execute(
            select(TransportRecord).where(TransportRecord.transport_id == rollback_id)
        )
        existing_record = existing_q.scalar_one_or_none()

        if existing_record:
            new_record = existing_record
            new_record.source_system = current_target
            new_record.target_system = current_source
            new_record.status = "in_progress"
            new_record.promoted_by = "rollback"
            new_record.promoted_at = datetime.utcnow()
            new_record.completed_at = None
            new_record.landscape = landscape
        else:
            new_record = TransportRecord(
                transport_id=rollback_id,
                description=f"Rollback of {transport_id} from {current_target} to {current_source}",
                source_system=current_target,
                target_system=current_source,
                status="in_progress",
                promoted_by="rollback",
                promoted_at=datetime.utcnow(),
                completed_at=None,
                landscape=landscape,
                validation_report={"rollback_status": "initiated"},
            )
            db.add(new_record)

        await db.commit()
        await db.refresh(new_record)

        # WebSocket broadcast
        from backend.core.websocket_manager import manager

        manager.add_event(
            event_type="TRANSPORT_ROLLBACK",
            message=f"Rollback initiated for {transport_id} from {current_target} to {current_source}",
            transport_id=rollback_id,
        )
        await manager.broadcast()

        # Slack notification
        try:
            await request.app.state.slack.notify_transport_rollback(
                transport_id=transport_id, system=current_target
            )
        except Exception as slack_err:
            logger.error(
                f"Error sending Slack notification for transport rollback: {slack_err}"
            )

        return {
            "id": str(new_record.id),
            "transport_id": new_record.transport_id,
            "status": new_record.status,
            "description": new_record.description,
            "source_system": new_record.source_system,
            "target_system": new_record.target_system,
            "promoted_by": new_record.promoted_by,
            "promoted_at": new_record.promoted_at.isoformat(),
            "landscape": new_record.landscape,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing rollback for transport {transport_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transport_id}")
async def get_transport_details(transport_id: str, db: AsyncSession = Depends(get_db)):
    """Get transport details by ID. Path param: transport_id. Returns transport record or 404. No side effects."""
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
            "completed_at": record.completed_at.isoformat()
            if record.completed_at
            else None,
            "validation_report": record.validation_report,
            "landscape": record.landscape,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transport details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_transport(transport_id: str):
    """Validate transport via ABAP inspection. Query param: transport_id. Returns inspection and validation report. No side effects."""
    try:
        from transport_runner.abap_inspector import ABAPInspector
        from transport_runner.transport_validator import TransportValidator

        inspector = ABAPInspector(
            sap_host=settings.SAP_BTP_HOST,
            client_id=settings.SAP_CLIENT_ID,
            client_secret=settings.SAP_CLIENT_SECRET,
        )

        inspection_result = await inspector.run_code_inspection(transport_id)
        objects = await inspector.validate_transport_objects(transport_id)

        validator = TransportValidator(objects)
        validation_result = validator.generate_report()

        return {
            "transport_id": transport_id,
            "inspection": inspection_result,
            "validation": validation_result,
            "overall_valid": validation_result.get("is_valid", False),
        }
    except Exception as e:
        logger.error(f"Error validating transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))

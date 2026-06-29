from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.database import PipelineRun
from backend.models.schemas import PipelineTriggerRequest
from backend.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


async def get_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        yield session


@router.get("/status")
async def get_pipeline_status(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(PipelineRun)
            .order_by(PipelineRun.triggered_at.desc())
            .limit(10)
        )
        runs = result.scalars().all()
        
        github_service = getattr(request.app.state, "github", None)
        
        last_runs = []
        for i, run in enumerate(runs):
            jobs = []
            if i < 3 and github_service:
                try:
                    raw_jobs = await github_service.get_run_jobs(run.run_id)
                    jobs = [{"name": j["name"], "status": j["status"]} for j in raw_jobs]
                except Exception as je:
                    logger.error(f"Error fetching jobs for run {run.run_id}: {je}")
            
            last_runs.append({
                "run_id": run.run_id,
                "branch": run.branch,
                "commit_sha": run.commit_sha,
                "status": run.status,
                "triggered_at": run.triggered_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "duration_seconds": run.duration_seconds,
                "transport_id": run.transport_id,
                "jobs": jobs
            })
            
        return {
            "current_status": runs[0].status if runs else "idle",
            "last_runs": last_runs
        }
    except Exception as e:
        logger.error(f"Error fetching pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_pipeline_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        
        return {
            "id": str(run.id),
            "run_id": run.run_id,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "status": run.status,
            "triggered_at": run.triggered_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_seconds": run.duration_seconds,
            "transport_id": run.transport_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pipeline run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_pipeline(request: Request, payload: PipelineTriggerRequest):
    github_service = getattr(request.app.state, "github", None)
    if not github_service:
        raise HTTPException(status_code=500, detail="GitHub service not available")
        
    branch = payload.branch
    success = await github_service.trigger_workflow("ci.yml", branch)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to trigger pipeline for branch {branch}")
        
    return {"message": f"Pipeline triggered on branch {branch}", "branch": branch}


@router.post("/sync")
async def sync_pipeline(request: Request, db: AsyncSession = Depends(get_db)):
    github_service = getattr(request.app.state, "github", None)
    if not github_service:
        raise HTTPException(status_code=500, detail="GitHub service not available")
        
    try:
        synced_count = await github_service.sync_runs_to_db(db)
        return {"synced": synced_count, "message": f"Synced {synced_count} runs from GitHub"}
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/jobs")
async def get_run_jobs(run_id: str, request: Request):
    github_service = getattr(request.app.state, "github", None)
    if not github_service:
        raise HTTPException(status_code=500, detail="GitHub service not available")
        
    try:
        jobs = await github_service.get_run_jobs(run_id)
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_pipeline_metrics(db: AsyncSession = Depends(get_db)):
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(
                func.date(PipelineRun.triggered_at).label('date'),
                PipelineRun.status,
                func.count(PipelineRun.id).label('count')
            )
            .where(PipelineRun.triggered_at >= thirty_days_ago)
            .group_by(func.date(PipelineRun.triggered_at), PipelineRun.status)
            .order_by(func.date(PipelineRun.triggered_at))
        )
        
        metrics = result.all()
        
        daily_metrics = {}
        for date, status, count in metrics:
            date_str = date.isoformat()
            if date_str not in daily_metrics:
                daily_metrics[date_str] = {"date": date_str, "success": 0, "failed": 0}
            if status == "success":
                daily_metrics[date_str]["success"] = count
            elif status == "failed":
                daily_metrics[date_str]["failed"] = count
        
        return list(daily_metrics.values())
    except Exception as e:
        logger.error(f"Error fetching pipeline metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

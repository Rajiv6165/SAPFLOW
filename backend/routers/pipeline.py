from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.database import PipelineRun
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
async def get_pipeline_status(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(PipelineRun)
            .order_by(PipelineRun.triggered_at.desc())
            .limit(10)
        )
        runs = result.scalars().all()
        
        return {
            "current_status": runs[0].status if runs else "idle",
            "last_runs": [
                {
                    "run_id": run.run_id,
                    "branch": run.branch,
                    "commit_sha": run.commit_sha,
                    "status": run.status,
                    "triggered_at": run.triggered_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "duration_seconds": run.duration_seconds,
                    "transport_id": run.transport_id
                }
                for run in runs
            ]
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
async def trigger_pipeline(branch: str = "main"):
    if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO:
        raise HTTPException(status_code=400, detail="GitHub credentials not configured")
    
    try:
        owner, repo = settings.GITHUB_REPO.split("/")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/ci.yml/dispatches",
                json={"ref": branch},
                headers={
                    "Authorization": f"token {settings.GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
        
        return {"message": f"Pipeline triggered on branch {branch}", "branch": branch}
    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")
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

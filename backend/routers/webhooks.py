import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.websocket_manager import manager
from backend.models.database import PipelineRun
from backend.routers.pipeline import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    body = await request.body()
    
    # 1. Verify Webhook Signature
    if not x_hub_signature_256.startswith("sha256="):
        logger.warning("Signature header does not start with sha256=")
        raise HTTPException(status_code=401, detail="Invalid signature format")
        
    signature = x_hub_signature_256.split("sha256=")[1]
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    computed_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    # 2. Parse payload
    try:
        payload = json.loads(body.decode())
    except Exception as e:
        logger.error(f"Failed to parse JSON webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    action = payload.get("action", "")
    logger.info(f"Received GitHub webhook: event={x_github_event}, action={action}")
    
    # 3. Handle Events
    if x_github_event == "workflow_run":
        workflow_run = payload.get("workflow_run", {})
        run_id = f"run-{workflow_run.get('id')}"
        branch = workflow_run.get("head_branch")
        commit_sha = workflow_run.get("head_sha")
        conclusion = workflow_run.get("conclusion")
        
        if action == "requested":
            # Start of pipeline
            stmt = select(PipelineRun).where(PipelineRun.run_id == run_id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            
            if not run:
                run = PipelineRun(
                    run_id=run_id,
                    branch=branch,
                    commit_sha=commit_sha,
                    status="running",
                    triggered_at=datetime.utcnow()
                )
                db.add(run)
            else:
                run.status = "running"
                run.triggered_at = datetime.utcnow()
                
            await db.commit()
            
            # Record WS event and broadcast
            manager.add_event(
                event_type="PIPELINE_STARTED",
                message=f"Pipeline run #{workflow_run.get('id')} started on branch {branch}",
                branch=branch
            )
            await manager.broadcast()
            logger.info(f"Pipeline status updated to running for run {run_id}")
            
        elif action == "completed":
            # Completion of pipeline
            stmt = select(PipelineRun).where(PipelineRun.run_id == run_id)
            res = await db.execute(stmt)
            run = res.scalar_one_or_none()
            
            mapped_status = "success" if conclusion == "success" else "failed"
            duration = workflow_run.get("duration")
            
            if duration is None:
                # Fallback: compute duration from payload timestamps
                created_at_str = workflow_run.get("created_at")
                updated_at_str = workflow_run.get("updated_at")
                if created_at_str and updated_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                        duration = int((updated_at - created_at).total_seconds())
                    except Exception as ex:
                        logger.error(f"Error parsing times: {ex}")
            
            if not run:
                triggered_at = datetime.utcnow()
                if duration:
                    triggered_at -= timedelta(seconds=duration)
                run = PipelineRun(
                    run_id=run_id,
                    branch=branch,
                    commit_sha=commit_sha,
                    status=mapped_status,
                    triggered_at=triggered_at,
                    completed_at=datetime.utcnow(),
                    duration_seconds=duration
                )
                db.add(run)
            else:
                run.status = mapped_status
                run.completed_at = datetime.utcnow()
                if duration:
                    run.duration_seconds = duration
                elif run.triggered_at:
                    run.duration_seconds = int((datetime.utcnow() - run.triggered_at).total_seconds())
            
            await db.commit()
            
            # Record WS event and broadcast
            event_type = "PIPELINE_PASSED" if mapped_status == "success" else "PIPELINE_FAILED"
            manager.add_event(
                event_type=event_type,
                message=f"Pipeline run #{workflow_run.get('id')} {mapped_status} on branch {branch}",
                branch=branch
            )
            await manager.broadcast()
            logger.info(f"Pipeline status updated to {mapped_status} for run {run_id}")
            
    elif x_github_event == "push":
        # Handle new commit push event
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        pusher = payload.get("pusher", {}).get("name", "GitHub")
        commits = payload.get("commits", [])
        commit_msg = commits[0].get("message", "New commit") if commits else "New commit"
        
        manager.add_event(
            event_type="PUSH",
            message=f"New commit by {pusher}: {commit_msg}",
            branch=branch
        )
        await manager.broadcast()
        logger.info(f"Received push event for branch {branch} by {pusher}")
        
    elif x_github_event == "workflow_job":
        # Log individual job updates
        workflow_job = payload.get("workflow_job", {})
        job_name = workflow_job.get("name", "Unknown Job")
        job_status = workflow_job.get("status", "")
        job_conclusion = workflow_job.get("conclusion", "")
        logger.info(f"Workflow Job Update: '{job_name}' is {job_status} ({job_conclusion or 'running'})")
        
    return {"received": True}

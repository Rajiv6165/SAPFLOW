import httpx
import logging
import random
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from backend.core.config import settings
from backend.models.database import PipelineRun
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Class-level mock database to simulate live pipeline progress
_mock_runs: List[Dict[str, Any]] = []

def _init_mock_runs():
    global _mock_runs
    if _mock_runs:
        return
    
    # Pre-populate with 15 runs matching seed.py, plus a few newer ones
    now = datetime.utcnow()
    
    # 8 success, 4 failed, 2 running, 1 pending
    setup = [
        {"status": "completed", "conclusion": "success", "branch": "main", "hours_ago": 144, "duration": 120},
        {"status": "completed", "conclusion": "success", "branch": "develop", "hours_ago": 120, "duration": 180},
        {"status": "completed", "conclusion": "success", "branch": "feature/mm-procurement", "hours_ago": 100, "duration": 95},
        {"status": "completed", "conclusion": "success", "branch": "develop", "hours_ago": 72, "duration": 220},
        {"status": "completed", "conclusion": "success", "branch": "main", "hours_ago": 68, "duration": 150},
        {"status": "completed", "conclusion": "success", "branch": "feature/fi-posting", "hours_ago": 55, "duration": 110},
        {"status": "completed", "conclusion": "success", "branch": "main", "hours_ago": 20, "duration": 240},
        {"status": "completed", "conclusion": "success", "branch": "hotfix/transport-fix", "hours_ago": 8, "duration": 85},
        
        {"status": "completed", "conclusion": "failure", "branch": "feature/fi-posting", "hours_ago": 96, "duration": 310},
        {"status": "completed", "conclusion": "failure", "branch": "develop", "hours_ago": 60, "duration": 290},
        {"status": "completed", "conclusion": "failure", "branch": "feature/mm-procurement", "hours_ago": 30, "duration": 145},
        {"status": "completed", "conclusion": "failure", "branch": "develop", "hours_ago": 10, "duration": 350},
        
        {"status": "in_progress", "conclusion": None, "branch": "feature/mm-procurement", "hours_ago": 0.5, "duration": None},
        {"status": "in_progress", "conclusion": None, "branch": "develop", "hours_ago": 0.2, "duration": None},
        {"status": "queued", "conclusion": None, "branch": "hotfix/transport-fix", "hours_ago": 0.05, "duration": None},
    ]
    
    def generate_sha():
        return "".join(random.choices("0123456789abcdef", k=7))
    
    for idx, item in enumerate(setup):
        triggered_at = now - timedelta(hours=item["hours_ago"])
        updated_at = triggered_at + timedelta(seconds=item["duration"]) if item["duration"] else now
        
        _mock_runs.append({
            "id": 1000 + idx,
            "name": "SAPFlow CI Pipeline",
            "status": item["status"],
            "conclusion": item["conclusion"],
            "head_branch": item["branch"],
            "head_sha": generate_sha(),
            "created_at": triggered_at.isoformat() + "Z",
            "updated_at": updated_at.isoformat() + "Z"
        })

class GitHubService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO
        _init_mock_runs()
        
    def _is_mock_mode(self) -> bool:
        return not self.token or "token" in self.token.lower() or self.token == ""

    async def get_workflow_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self._is_mock_mode():
            logger.info("GitHub API in mock mode. Returning mock workflow runs.")
            # Sort mock runs by created_at descending
            sorted_runs = sorted(_mock_runs, key=lambda x: x["created_at"], reverse=True)
            result = []
            for run in sorted_runs[:limit]:
                result.append({
                    "id": run["id"],
                    "name": run["name"],
                    "status": self._map_status(run["status"], run["conclusion"]),
                    "conclusion": run["conclusion"],
                    "branch": run["head_branch"],
                    "head_sha": run["head_sha"],
                    "created_at": run["created_at"],
                    "updated_at": run["updated_at"]
                })
            return result

        owner, repo = self.repo.split("/")
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params={"per_page": limit})
                response.raise_for_status()
                data = response.json()
                runs = data.get("workflow_runs", [])
                
                result = []
                for run in runs:
                    result.append({
                        "id": run["id"],
                        "name": run["name"],
                        "status": self._map_status(run["status"], run.get("conclusion")),
                        "conclusion": run.get("conclusion"),
                        "branch": run["head_branch"],
                        "head_sha": run["head_sha"],
                        "created_at": run["created_at"],
                        "updated_at": run["updated_at"]
                    })
                return result
            except Exception as e:
                logger.error(f"Error fetching workflow runs from GitHub API: {e}")
                # Fallback to mock on error
                return await self.get_workflow_runs(limit)

    async def get_run_jobs(self, run_id: Any) -> List[Dict[str, Any]]:
        # Normalize run_id
        normalized_id = run_id
        if isinstance(run_id, str) and run_id.startswith("run-"):
            try:
                normalized_id = int(run_id.split("-")[1])
            except ValueError:
                pass

        if self._is_mock_mode():
            logger.info(f"GitHub API in mock mode. Returning mock jobs for run {normalized_id}.")
            return self._generate_mock_jobs(normalized_id)

        owner, repo = self.repo.split("/")
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{normalized_id}/jobs"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs", [])
                
                result = []
                for job in jobs:
                    result.append({
                        "name": job["name"],
                        "status": self._map_status(job["status"], job.get("conclusion")),
                        "conclusion": job.get("conclusion"),
                        "started_at": job["started_at"],
                        "completed_at": job.get("completed_at"),
                        "steps": [
                            {"name": step["name"], "status": self._map_status(step["status"], step.get("conclusion"))}
                            for step in job.get("steps", [])
                        ]
                    })
                return result
            except Exception as e:
                logger.error(f"Error fetching run jobs from GitHub API: {e}")
                return self._generate_mock_jobs(normalized_id)

    async def trigger_workflow(self, workflow_id: str, branch: str, inputs: Optional[Dict[str, Any]] = None) -> bool:
        if self._is_mock_mode():
            logger.info(f"GitHub API in mock mode. Simulating dispatch trigger for {workflow_id} on {branch}.")
            # Simulate a new run triggered
            new_id = 1000 + len(_mock_runs)
            now_iso = datetime.utcnow().isoformat() + "Z"
            
            _mock_runs.append({
                "id": new_id,
                "name": "SAPFlow CI Pipeline",
                "status": "queued",
                "conclusion": None,
                "head_branch": branch,
                "head_sha": "".join(random.choices("0123456789abcdef", k=7)),
                "created_at": now_iso,
                "updated_at": now_iso
            })
            return True

        owner, repo = self.repo.split("/")
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"ref": branch}
        if inputs:
            payload["inputs"] = inputs
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                return response.status_code == 204
            except Exception as e:
                logger.error(f"Error triggering workflow dispatch: {e}")
                return False

    async def sync_runs_to_db(self, db_session: AsyncSession) -> int:
        try:
            runs = await self.get_workflow_runs(20)
            synced_count = 0
            
            for run in runs:
                run_db_id = f"run-{run['id']}"
                
                # Check if exists
                stmt = select(PipelineRun).where(PipelineRun.run_id == run_db_id)
                res = await db_session.execute(stmt)
                db_run = res.scalar_one_or_none()
                
                triggered_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                completed_at = None
                if run["updated_at"] and run["status"] in ["success", "failed"]:
                    completed_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                
                duration_seconds = None
                if triggered_at and completed_at:
                    duration_seconds = int((completed_at - triggered_at).total_seconds())
                
                if not db_run:
                    db_run = PipelineRun(
                        run_id=run_db_id,
                        branch=run["branch"],
                        commit_sha=run["head_sha"],
                        status=run["status"],
                        triggered_at=triggered_at,
                        completed_at=completed_at,
                        duration_seconds=duration_seconds,
                        transport_id=None # Optionally extract from commit message if standard
                    )
                    db_session.add(db_run)
                    synced_count += 1
                else:
                    db_run.status = run["status"]
                    db_run.completed_at = completed_at
                    db_run.duration_seconds = duration_seconds
                    db_run.branch = run["branch"]
                    db_run.commit_sha = run["head_sha"]
                    synced_count += 1
                    
            await db_session.commit()
            return synced_count
        except Exception as e:
            logger.error(f"Error in sync_runs_to_db: {e}")
            await db_session.rollback()
            return 0

    def _map_status(self, gh_status: str, conclusion: Optional[str]) -> str:
        if gh_status == "in_progress":
            return "running"
        elif gh_status == "completed":
            if conclusion == "success":
                return "success"
            elif conclusion == "failure":
                return "failed"
            elif conclusion == "skipped":
                return "skipped"
            return "failed"
        elif gh_status == "queued":
            return "pending"
        return "pending"

    def _generate_mock_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        # Find the run status from in-memory mock runs
        run = next((r for r in _mock_runs if r["id"] == run_id), None)
        run_status = run["status"] if run else "completed"
        run_conclusion = run["conclusion"] if run else "success"
        
        # Determine status of jobs based on overall run status
        if run_status == "completed":
            if run_conclusion == "success":
                jobs_status = {
                    "code-quality": ("success", "success", ["success"] * 7),
                    "abap-validation": ("success", "success", ["success"] * 5),
                    "docker-build": ("success", "success", ["success"] * 4),
                    "notify": ("success", "success", ["success"] * 1),
                    "report-to-sapflow": ("success", "success", ["success"] * 1)
                }
            else: # failure
                jobs_status = {
                    "code-quality": ("success", "success", ["success"] * 7),
                    "abap-validation": ("failed", "failure", ["success", "success", "success", "failed", "skipped"]),
                    "docker-build": ("skipped", "skipped", ["skipped"] * 4),
                    "notify": ("success", "success", ["success"] * 1),
                    "report-to-sapflow": ("success", "success", ["success"] * 1)
                }
        elif run_status == "in_progress" or run_status == "running":
            jobs_status = {
                "code-quality": ("success", "success", ["success"] * 7),
                "abap-validation": ("running", None, ["success", "success", "running", "pending", "pending"]),
                "docker-build": ("pending", None, ["pending"] * 4),
                "notify": ("pending", None, ["pending"] * 1),
                "report-to-sapflow": ("pending", None, ["pending"] * 1)
            }
        else: # queued / pending
            jobs_status = {
                "code-quality": ("pending", None, ["pending"] * 7),
                "abap-validation": ("pending", None, ["pending"] * 5),
                "docker-build": ("pending", None, ["pending"] * 4),
                "notify": ("pending", None, ["pending"] * 1),
                "report-to-sapflow": ("pending", None, ["pending"] * 1)
            }

        job_steps = {
            "code-quality": [
                "Checkout code", "Set up Python", "Install dependencies", 
                "Run flake8", "Run black check", "Run pytest with coverage", "Upload coverage"
            ],
            "abap-validation": [
                "Checkout code", "Set up Python", "Install dependencies", 
                "Run ABAP Inspector", "Post GitHub status"
            ],
            "docker-build": [
                "Checkout code", "Configure AWS credentials", "Login to Amazon ECR", 
                "Build and push Docker image"
            ],
            "notify": [
                "Send Slack notification"
            ],
            "report-to-sapflow": [
                "Report pipeline result to SAPFlow"
            ]
        }

        result = []
        for job_name, (status, conclusion, step_statuses) in jobs_status.items():
            steps = []
            for step_name, step_status in zip(job_steps[job_name], step_statuses):
                steps.append({
                    "name": step_name,
                    "status": step_status
                })
            
            # Simple duration simulation
            duration = random.randint(15, 60) if status == "success" else (random.randint(5, 15) if status == "failed" else 0)
            
            result.append({
                "name": job_name,
                "status": status,
                "conclusion": conclusion,
                "duration_seconds": duration,
                "steps": steps
            })
            
        return result

import asyncio
import os
import sys
import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Setup path so imports work inside and outside docker container
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.database import Base, PipelineRun, TransportRecord, SystemHealthSnapshot, engine
    from core.config import settings
except ImportError:
    from backend.models.database import Base, PipelineRun, TransportRecord, SystemHealthSnapshot, engine
    from backend.core.config import settings


async def seed_database():
    print("Connecting to database using shared engine to seed...")
    
    async with AsyncSession(engine) as session:
        # 1. Clear existing data
        print("Clearing existing database tables...")
        await session.execute(delete(PipelineRun))
        await session.execute(delete(TransportRecord))
        await session.execute(delete(SystemHealthSnapshot))
        await session.commit()

        now = datetime.utcnow()

        # 2. Seed TransportRecord records (10 total: 4 DEFAULT, 3 FINANCE, 3 LOGISTICS)
        # 3 active transports in progress/pending
        print("Seeding transport records...")
        transports_data = [
            # LOGISTICS (3)
            {"transport_id": "DEVK900001", "description": "MM procurement config update", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "rajiv.thakker", "hours_ago": 14, "landscape": "LOGISTICS"},
            {"transport_id": "DEVK900003", "description": "SD pricing procedure fix", "source_system": "DEV", "target_system": "QA", "status": "failed", "promoted_by": "rajiv.thakker", "hours_ago": 9, "landscape": "LOGISTICS"},
            {"transport_id": "DEVK900010", "description": "MM routing config update", "source_system": "DEV", "target_system": "QA", "status": "in_progress", "promoted_by": "rajiv.thakker", "hours_ago": 2, "landscape": "LOGISTICS"}, # Active 1
            
            # FINANCE (3)
            {"transport_id": "DEVK900002", "description": "FI document type change", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "admin", "hours_ago": 12, "landscape": "FINANCE"},
            {"transport_id": "DEVK900007", "description": "FI tax classification schema", "source_system": "DEV", "target_system": "QA", "status": "pending", "promoted_by": "admin", "hours_ago": 4, "landscape": "FINANCE"}, # Active 2
            {"transport_id": "DEVK900008", "description": "CO cost center hierarchy update", "source_system": "QA", "target_system": "PROD", "status": "success", "promoted_by": "ci-pipeline", "hours_ago": 6, "landscape": "FINANCE"},
            
            # DEFAULT (4)
            {"transport_id": "DEVK900004", "description": "ABAP custom report Z_BASIS_CHECK", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "ci-pipeline", "hours_ago": 18, "landscape": "DEFAULT"},
            {"transport_id": "DEVK900005", "description": "BASIS system parameter change", "source_system": "QA", "target_system": "PROD", "status": "success", "promoted_by": "admin", "hours_ago": 15, "landscape": "DEFAULT"},
            {"transport_id": "DEVK900006", "description": "PP routing configuration update", "source_system": "QA", "target_system": "PROD", "status": "in_progress", "promoted_by": "rajiv.thakker", "hours_ago": 8, "landscape": "DEFAULT"}, # Active 3
            {"transport_id": "DEVK900009", "description": "WM storage bin definition", "source_system": "QA", "target_system": "PROD", "status": "failed", "promoted_by": "rajiv.thakker", "hours_ago": 10, "landscape": "DEFAULT"},
        ]

        for t in transports_data:
            promoted_at = now - timedelta(hours=t["hours_ago"])
            completed_at = promoted_at + timedelta(seconds=random.randint(60, 300)) if t["status"] in ["success", "failed"] else None
            record = TransportRecord(
                id=uuid.uuid4(),
                transport_id=t["transport_id"],
                description=t["description"],
                source_system=t["source_system"],
                target_system=t["target_system"],
                status=t["status"],
                promoted_by=t["promoted_by"],
                promoted_at=promoted_at,
                completed_at=completed_at,
                validation_report={"validations_checked": 4, "errors": 0 if t["status"] == "success" else 2},
                landscape=t["landscape"]
            )
            session.add(record)
        
        await session.commit()

        # 3. Seed PipelineRun records (15 total: 12 today, 3 in past)
        # Success rate today: exactly 83% (10 successes out of 12 runs today)
        # Mix of success/failed, currently 1 running today.
        print("Seeding pipeline runs...")
        pipeline_runs_setup = [
            # 3 runs in past (yesterday/before)
            {"status": "success", "branch": "main", "hours_ago": 48, "duration": 120, "transport_id": "DEVK900001"},
            {"status": "success", "branch": "develop", "hours_ago": 36, "duration": 180, "transport_id": "DEVK900002"},
            {"status": "failed", "branch": "feature/fi-posting", "hours_ago": 30, "duration": 220, "transport_id": "DEVK900003"},
            
            # 12 runs today (10 success, 1 failed, 1 running)
            {"status": "success", "branch": "feature/mm-procurement", "hours_ago": 10, "duration": 95, "transport_id": "DEVK900004"},
            {"status": "success", "branch": "develop", "hours_ago": 9, "duration": 220, "transport_id": "DEVK900005"},
            {"status": "success", "branch": "main", "hours_ago": 8, "duration": 150, "transport_id": "DEVK900006"},
            {"status": "success", "branch": "feature/fi-posting", "hours_ago": 7, "duration": 110, "transport_id": None},
            {"status": "success", "branch": "main", "hours_ago": 6, "duration": 240, "transport_id": "DEVK900008"},
            {"status": "success", "branch": "hotfix/transport-fix", "hours_ago": 5, "duration": 85, "transport_id": None},
            {"status": "success", "branch": "develop", "hours_ago": 4, "duration": 140, "transport_id": None},
            {"status": "success", "branch": "feature/mm-procurement", "hours_ago": 3, "duration": 130, "transport_id": None},
            {"status": "success", "branch": "develop", "hours_ago": 2, "duration": 160, "transport_id": None},
            {"status": "success", "branch": "main", "hours_ago": 1, "duration": 155, "transport_id": None},
            
            # Failed run today
            {"status": "failed", "branch": "develop", "hours_ago": 11, "duration": 290, "transport_id": "DEVK900009"},
            
            # Running run today
            {"status": "running", "branch": "feature/mm-procurement", "hours_ago": 0.2, "duration": None, "transport_id": "DEVK900010"},
        ]

        def generate_sha():
            return "".join(random.choices("0123456789abcdef", k=7))

        for idx, r in enumerate(pipeline_runs_setup):
            triggered_at = now - timedelta(hours=r["hours_ago"])
            completed_at = triggered_at + timedelta(seconds=r["duration"]) if r["duration"] else None
            
            run = PipelineRun(
                id=uuid.uuid4(),
                run_id=f"run-{1000 + idx}",
                branch=r["branch"],
                commit_sha=generate_sha(),
                status=r["status"],
                triggered_at=triggered_at,
                completed_at=completed_at,
                duration_seconds=r["duration"],
                transport_id=r["transport_id"]
            )
            session.add(run)

        # 4. Seed SystemHealthSnapshot records (50 total)
        # Latest must be: CPU 34%, Memory 67%, 47 active users, 234ms response time
        print("Seeding system health snapshots...")
        
        # Latest snapshot
        latest_snapshot = SystemHealthSnapshot(
            id=uuid.uuid4(),
            recorded_at=now,
            cpu_percent=34.0,
            memory_percent=67.0,
            active_users=47,
            avg_response_ms=234,
            status="healthy"
        )
        session.add(latest_snapshot)
        
        # Remaining 49 snapshots
        for i in range(1, 50):
            recorded_at = now - timedelta(minutes=5 * i)
            cpu = round(random.uniform(20.0, 60.0), 2)
            mem = round(random.uniform(50.0, 75.0), 2)
            users = random.randint(30, 80)
            resp = random.randint(180, 400)
            
            status = "healthy"
            if cpu >= 80 or mem >= 85:
                status = "degraded"
            
            snapshot = SystemHealthSnapshot(
                id=uuid.uuid4(),
                recorded_at=recorded_at,
                cpu_percent=cpu,
                memory_percent=mem,
                active_users=users,
                avg_response_ms=resp,
                status=status
            )
            session.add(snapshot)

        await session.commit()
        print("✅ Database tables seeded successfully")

        # 5. Seed events in WebSocket manager event_log
        try:
            from backend.core.websocket_manager import manager
            manager.event_log = []
            
            # Add 5 events of different types
            # PUSH
            manager.add_event(
                event_type="PUSH",
                message="New commit by rajiv.thakker: Fix routing logic for MM inventory",
                branch="feature/mm-procurement"
            )
            # PIPELINE_STARTED
            manager.add_event(
                event_type="PIPELINE_STARTED",
                message="Pipeline run #1014 started on branch develop",
                branch="develop"
            )
            # PIPELINE_FAILED
            manager.add_event(
                event_type="PIPELINE_FAILED",
                message="Pipeline run #1011 failed on branch develop",
                branch="develop"
            )
            # TRANSPORT_PROMOTED
            manager.add_event(
                event_type="TRANSPORT_PROMOTED",
                message="Transport DEVK900008 promoted to PROD",
                transport_id="DEVK900008"
            )
            # TRANSPORT_ROLLBACK
            manager.add_event(
                event_type="TRANSPORT_ROLLBACK",
                message="Transport DEVK900003 rollback initiated for QA",
                transport_id="DEVK900003"
            )
            print("✅ WebSocket events seeded in ConnectionManager")
        except Exception as ws_err:
            print(f"Skipped seeding websocket events: {ws_err}")


if __name__ == "__main__":
    asyncio.run(seed_database())

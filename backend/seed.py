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
    from models.database import Base, PipelineRun, TransportRecord, SystemHealthSnapshot
    from core.config import settings
except ImportError:
    from backend.models.database import Base, PipelineRun, TransportRecord, SystemHealthSnapshot
    from backend.core.config import settings


async def seed_database():
    # Make sure we use +asyncpg dialect
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to database to seed: {db_url.split('@')[-1]}")
    engine = create_async_engine(db_url, echo=False)
    
    async with AsyncSession(engine) as session:
        # 1. Clear existing data
        print("Clearing existing database tables...")
        await session.execute(delete(PipelineRun))
        await session.execute(delete(TransportRecord))
        await session.execute(delete(SystemHealthSnapshot))
        await session.commit()

        now = datetime.utcnow()

        # 2. Seed TransportRecord records (10 total)
        print("Seeding transport records...")
        transports_data = [
            {"transport_id": "DEVK900001", "description": "MM procurement config update", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "rajiv.thakker", "hours_ago": 144},
            {"transport_id": "DEVK900002", "description": "FI document type change", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "admin", "hours_ago": 120},
            {"transport_id": "DEVK900003", "description": "SD pricing procedure fix", "source_system": "DEV", "target_system": "QA", "status": "failed", "promoted_by": "rajiv.thakker", "hours_ago": 96},
            {"transport_id": "DEVK900004", "description": "ABAP custom report Z_MM_STOCK", "source_system": "DEV", "target_system": "QA", "status": "success", "promoted_by": "ci-pipeline", "hours_ago": 72},
            {"transport_id": "DEVK900005", "description": "BASIS system parameter change", "source_system": "QA", "target_system": "PROD", "status": "success", "promoted_by": "admin", "hours_ago": 68},
            {"transport_id": "DEVK900006", "description": "PP routing configuration update", "source_system": "DEV", "target_system": "QA", "status": "in_progress", "promoted_by": "rajiv.thakker", "hours_ago": 48},
            {"transport_id": "DEVK900007", "description": "QM inspection plan adjustment", "source_system": "DEV", "target_system": "QA", "status": "pending", "promoted_by": "admin", "hours_ago": 24},
            {"transport_id": "DEVK900008", "description": "CO cost center hierarchy update", "source_system": "QA", "target_system": "PROD", "status": "success", "promoted_by": "ci-pipeline", "hours_ago": 20},
            {"transport_id": "DEVK900009", "description": "WM storage bin definition", "source_system": "QA", "target_system": "PROD", "status": "failed", "promoted_by": "rajiv.thakker", "hours_ago": 10},
            {"transport_id": "DEVK900010", "description": "HR payroll schema correction", "source_system": "QA", "target_system": "PROD", "status": "in_progress", "promoted_by": "admin", "hours_ago": 2},
        ]

        transport_records = []
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
                validation_report={"validations_checked": 4, "errors": 0 if t["status"] == "success" else 2}
            )
            session.add(record)
            transport_records.append(record)
        
        await session.commit()

        # 3. Seed PipelineRun records (15 total)
        print("Seeding pipeline runs...")
        # 8 success, 4 failed, 2 running, 1 pending
        pipeline_runs_setup = [
            # Successes (8)
            {"status": "success", "branch": "main", "hours_ago": 144, "duration": 120, "transport_id": "DEVK900001"},
            {"status": "success", "branch": "develop", "hours_ago": 120, "duration": 180, "transport_id": "DEVK900002"},
            {"status": "success", "branch": "feature/mm-procurement", "hours_ago": 100, "duration": 95, "transport_id": None},
            {"status": "success", "branch": "develop", "hours_ago": 72, "duration": 220, "transport_id": "DEVK900004"},
            {"status": "success", "branch": "main", "hours_ago": 68, "duration": 150, "transport_id": "DEVK900005"},
            {"status": "success", "branch": "feature/fi-posting", "hours_ago": 55, "duration": 110, "transport_id": None},
            {"status": "success", "branch": "main", "hours_ago": 20, "duration": 240, "transport_id": "DEVK900008"},
            {"status": "success", "branch": "hotfix/transport-fix", "hours_ago": 8, "duration": 85, "transport_id": None},
            
            # Failed (4)
            {"status": "failed", "branch": "feature/fi-posting", "hours_ago": 96, "duration": 310, "transport_id": "DEVK900003"},
            {"status": "failed", "branch": "develop", "hours_ago": 60, "duration": 290, "transport_id": None},
            {"status": "failed", "branch": "feature/mm-procurement", "hours_ago": 30, "duration": 145, "transport_id": None},
            {"status": "failed", "branch": "develop", "hours_ago": 10, "duration": 350, "transport_id": "DEVK900009"},
            
            # Running (2)
            {"status": "running", "branch": "feature/mm-procurement", "hours_ago": 0.5, "duration": None, "transport_id": "DEVK900006"},
            {"status": "running", "branch": "develop", "hours_ago": 0.2, "duration": None, "transport_id": "DEVK900010"},
            
            # Pending (1)
            {"status": "pending", "branch": "hotfix/transport-fix", "hours_ago": 0.05, "duration": None, "transport_id": "DEVK900007"},
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
        print("Seeding system health snapshots...")
        for i in range(50):
            recorded_at = now - timedelta(minutes=5 * i)
            cpu = round(random.uniform(23.0, 78.0), 2)
            mem = round(random.uniform(41.0, 87.0), 2)
            users = random.randint(12, 156)
            resp = random.randint(180, 890)
            
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
        print("✅ Database seeded successfully")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_database())

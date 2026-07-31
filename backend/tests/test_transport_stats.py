import os
import pytest
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.models.database import TransportRecord


def test_transport_stats_calculation():
    """Test transport stats computation logic."""
    now = datetime.utcnow()
    records = [
        TransportRecord(
            transport_id="T1",
            description="desc1",
            source_system="DEV",
            target_system="QA",
            status="success",
            promoted_by="user",
            promoted_at=now - timedelta(seconds=200),
            completed_at=now - timedelta(seconds=100),
            landscape="FINANCE",
        ),
        TransportRecord(
            transport_id="T2",
            description="desc2",
            source_system="DEV",
            target_system="QA",
            status="failed",
            promoted_by="user",
            promoted_at=now - timedelta(seconds=100),
            completed_at=now - timedelta(seconds=50),
            landscape="FINANCE",
        ),
        TransportRecord(
            transport_id="T1_ROLLBACK",
            description="rollback desc",
            source_system="QA",
            target_system="DEV",
            status="in_progress",
            promoted_by="rollback",
            promoted_at=now - timedelta(seconds=10),
            completed_at=None,
            landscape="FINANCE",
        ),
    ]

    finance_records = [r for r in records if r.landscape == "FINANCE"]
    total_transports = len(finance_records)
    successes = len([r for r in finance_records if r.status == "success"])
    rollbacks = len(
        [
            r
            for r in finance_records
            if "_ROLLBACK" in r.transport_id or r.promoted_by == "rollback"
        ]
    )

    durations = [
        (r.completed_at - r.promoted_at).total_seconds()
        for r in finance_records
        if r.completed_at and r.promoted_at
    ]
    avg_dur = sum(durations) / len(durations) if durations else 0.0

    success_rate = (successes / total_transports) * 100

    assert total_transports == 3
    assert successes == 1
    assert rollbacks == 1
    assert round(success_rate, 2) == 33.33
    assert round(avg_dur, 2) == 75.0

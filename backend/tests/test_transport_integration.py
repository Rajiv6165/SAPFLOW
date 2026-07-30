import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from backend.main import app
from backend.models.database import Base, TransportRecord
from backend.routers.transport import get_db


# ─── Dummy Slack Service Mock ──────────────────────────────────────────────────

class DummySlackService:
    async def notify_transport_promoted(self, transport_id: str, source: str, target: str, promoted_by: str) -> bool:
        return True

    async def notify_transport_rollback(self, transport_id: str, system: str) -> bool:
        return True


# ─── Test Fixture Setup Helper ─────────────────────────────────────────────────

async def setup_test_app_and_db():
    """Sets up an in-memory SQLite database and yields a configured AsyncClient."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    test_engine = create_async_engine(test_db_url, connect_args={"check_same_thread": False})
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    testing_session_local = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.slack = DummySlackService()
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    return client, testing_session_local, test_engine


# ─── Integration Tests ─────────────────────────────────────────────────────────

def test_successful_promote_dev_to_qa():
    """Test successful promotion of transport from DEV to QA."""
    async def run():
        client, session_maker, engine = await setup_test_app_and_db()
        try:
            payload = {
                "transport_id": "DEVK900123",
                "source_system": "DEV",
                "target_system": "QA",
                "promoted_by": "developer1",
                "landscape": "FINANCE"
            }
            
            response = await client.post("/api/v1/transport/promote", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["transport_id"] == "DEVK900123"
            assert data["status"] == "success"
            assert data["landscape"] == "FINANCE"

            # Verify record created in DB
            async with session_maker() as session:
                res = await session.execute(
                    select(TransportRecord).where(TransportRecord.transport_id == "DEVK900123")
                )
                record = res.scalar_one_or_none()
                assert record is not None
                assert record.source_system == "DEV"
                assert record.target_system == "QA"
                assert record.status == "success"
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(run())


def test_successful_rollback_qa_to_dev():
    """Test successful rollback of a promoted transport from QA back to DEV."""
    async def run():
        client, session_maker, engine = await setup_test_app_and_db()
        try:
            # 1. First promote DEV -> QA
            promote_payload = {
                "transport_id": "DEVK900123",
                "source_system": "DEV",
                "target_system": "QA",
                "promoted_by": "developer1",
                "landscape": "FINANCE"
            }
            promote_res = await client.post("/api/v1/transport/promote", json=promote_payload)
            assert promote_res.status_code == 200

            # 2. Initiate Rollback
            rollback_res = await client.post("/api/v1/transport/DEVK900123/rollback")
            assert rollback_res.status_code == 200

            data = rollback_res.json()
            assert data["transport_id"] == "DEVK900123_ROLLBACK"
            assert data["source_system"] == "QA"
            assert data["target_system"] == "DEV"
            assert data["promoted_by"] == "rollback"
            assert data["status"] == "in_progress"

            # Verify rollback record in DB
            async with session_maker() as session:
                res = await session.execute(
                    select(TransportRecord).where(TransportRecord.transport_id == "DEVK900123_ROLLBACK")
                )
                rollback_record = res.scalar_one_or_none()
                assert rollback_record is not None
                assert rollback_record.source_system == "QA"
                assert rollback_record.target_system == "DEV"
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(run())


def test_promoting_already_promoted_transport_fails():
    """Test that attempting to promote an already-promoted transport fails with HTTP 400."""
    async def run():
        client, session_maker, engine = await setup_test_app_and_db()
        try:
            payload = {
                "transport_id": "DEVK900123",
                "source_system": "DEV",
                "target_system": "QA",
                "promoted_by": "developer1",
                "landscape": "DEFAULT"
            }
            
            # Initial promotion (should succeed)
            res1 = await client.post("/api/v1/transport/promote", json=payload)
            assert res1.status_code == 200

            # Duplicate promotion attempt to same target (should fail)
            res2 = await client.post("/api/v1/transport/promote", json=payload)
            assert res2.status_code == 400
            
            data = res2.json()
            assert "already promoted" in data["detail"]
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(run())


def test_rollback_without_promotion_history_fails():
    """Test that attempting to rollback a transport with no promotion history fails with HTTP 404."""
    async def run():
        client, session_maker, engine = await setup_test_app_and_db()
        try:
            response = await client.post("/api/v1/transport/DEVK999999/rollback")
            assert response.status_code == 404
            
            data = response.json()
            assert "Transport not found" in data["detail"]
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(run())


def test_rollback_unsuccessful_transport_fails():
    """Test that attempting to rollback a transport that is not in 'success' status fails with HTTP 400."""
    async def run():
        client, session_maker, engine = await setup_test_app_and_db()
        try:
            # Manually insert a failed transport record into DB
            async with session_maker() as session:
                failed_record = TransportRecord(
                    transport_id="DEVK900789",
                    description="Failed Transport",
                    source_system="DEV",
                    target_system="QA",
                    status="failed",
                    promoted_by="developer1",
                    landscape="DEFAULT"
                )
                session.add(failed_record)
                await session.commit()

            response = await client.post("/api/v1/transport/DEVK900789/rollback")
            assert response.status_code == 400
            assert "Can only rollback successful transports" in response.json()["detail"]
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(run())

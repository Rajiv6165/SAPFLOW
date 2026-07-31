import os
import hmac
import hashlib
import json
import asyncio
import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.config import settings
from backend.models.database import Base
from backend.routers.pipeline import get_db


class DummySlackService:
    async def notify_pipeline_result(self, branch: str, status: str, duration: int, run_url: str = "", commit: str = "") -> bool:
        return True


async def setup_test_app_and_db(monkeypatch, test_secret="test-mocked-github-secret-99"):
    # Mock the GITHUB_WEBHOOK_SECRET in test config
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", test_secret)

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
    return client, test_secret, test_engine, testing_session_local


def test_valid_signature_passes(monkeypatch):
    """Verify that a request with a valid HMAC-SHA256 signature is accepted with HTTP 200."""
    async def run():
        client, secret, engine, _ = await setup_test_app_and_db(monkeypatch)
        try:
            payload_dict = {
                "action": "completed",
                "workflow_run": {
                    "id": 98765,
                    "name": "SAPFlow CI",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "1234567890abcdef"
                }
            }
            body_bytes = json.dumps(payload_dict).encode("utf-8")
            valid_signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

            response = await client.post(
                "/api/v1/webhooks/github",
                content=body_bytes,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "X-Hub-Signature-256": f"sha256={valid_signature}",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 200
            assert response.json() == {"received": True}
        finally:
            await client.aclose()
            await engine.dispose()
            app.dependency_overrides.clear()

    asyncio.run(run())


def test_missing_signature_header_rejected_401(monkeypatch):
    """Verify that a request missing the X-Hub-Signature-256 header is rejected with HTTP 401."""
    async def run():
        client, _, engine, _ = await setup_test_app_and_db(monkeypatch)
        try:
            payload_dict = {"action": "completed", "workflow_run": {"id": 123}}
            body_bytes = json.dumps(payload_dict).encode("utf-8")

            response = await client.post(
                "/api/v1/webhooks/github",
                content=body_bytes,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Missing signature header"
        finally:
            await client.aclose()
            await engine.dispose()
            app.dependency_overrides.clear()

    asyncio.run(run())


def test_tampered_payload_with_stale_signature_rejected(monkeypatch):
    """Verify that sending a tampered payload with a signature computed for the original payload is rejected with HTTP 401."""
    async def run():
        client, secret, engine, _ = await setup_test_app_and_db(monkeypatch)
        try:
            original_payload = {
                "action": "requested",
                "workflow_run": {
                    "id": 55555,
                    "head_branch": "main",
                    "head_sha": "original_sha_123"
                }
            }
            original_bytes = json.dumps(original_payload).encode("utf-8")
            stale_signature = hmac.new(secret.encode("utf-8"), original_bytes, hashlib.sha256).hexdigest()

            # Tamper with the payload after signature computation
            tampered_payload = {
                "action": "completed",
                "workflow_run": {
                    "id": 55555,
                    "head_branch": "main",
                    "head_sha": "tampered_sha_999"
                }
            }
            tampered_bytes = json.dumps(tampered_payload).encode("utf-8")

            response = await client.post(
                "/api/v1/webhooks/github",
                content=tampered_bytes,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "X-Hub-Signature-256": f"sha256={stale_signature}",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid webhook signature"
        finally:
            await client.aclose()
            await engine.dispose()
            app.dependency_overrides.clear()

    asyncio.run(run())


def test_invalid_signature_format_rejected_401(monkeypatch):
    """Verify that a signature header not starting with 'sha256=' is rejected with HTTP 401."""
    async def run():
        client, secret, engine, _ = await setup_test_app_and_db(monkeypatch)
        try:
            body_bytes = json.dumps({"action": "completed"}).encode("utf-8")
            raw_signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

            response = await client.post(
                "/api/v1/webhooks/github",
                content=body_bytes,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "X-Hub-Signature-256": raw_signature,  # missing sha256= prefix
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid signature format"
        finally:
            await client.aclose()
            await engine.dispose()
            app.dependency_overrides.clear()

    asyncio.run(run())


def test_wrong_secret_signature_rejected_401(monkeypatch):
    """Verify that a payload signed with a different secret than configured is rejected with HTTP 401."""
    async def run():
        client, _, engine, _ = await setup_test_app_and_db(monkeypatch)
        try:
            body_bytes = json.dumps({"action": "completed"}).encode("utf-8")
            wrong_secret_signature = hmac.new(b"wrong-secret", body_bytes, hashlib.sha256).hexdigest()

            response = await client.post(
                "/api/v1/webhooks/github",
                content=body_bytes,
                headers={
                    "X-GitHub-Event": "workflow_run",
                    "X-Hub-Signature-256": f"sha256={wrong_secret_signature}",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid webhook signature"
        finally:
            await client.aclose()
            await engine.dispose()
            app.dependency_overrides.clear()

    asyncio.run(run())

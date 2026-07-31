import os
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.core.config import settings
from backend.services.github_service import GitHubService


def test_mock_mode_when_token_is_missing_or_placeholder(monkeypatch):
    """Verify GitHubService enters mock mode when token is empty, None, or placeholder."""
    for empty_token in ["", None, "placeholder_token", "YOUR_GITHUB_TOKEN"]:
        monkeypatch.setattr(settings, "GITHUB_TOKEN", empty_token)
        service = GitHubService()
        assert service._is_mock_mode() is True


def test_mock_data_fallback_returns_mock_workflow_runs(monkeypatch):
    """Verify get_workflow_runs returns mock data when no credentials are set."""

    async def run():
        monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
        service = GitHubService()

        runs = await service.get_workflow_runs(limit=5)
        assert isinstance(runs, list)
        assert len(runs) <= 5
        assert len(runs) > 0
        first_run = runs[0]
        assert "id" in first_run
        assert "name" in first_run
        assert "status" in first_run
        assert "branch" in first_run

    asyncio.run(run())


def test_mock_data_fallback_returns_mock_jobs(monkeypatch):
    """Verify get_run_jobs returns mock job steps when no credentials are set."""

    async def run():
        monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
        service = GitHubService()

        jobs = await service.get_run_jobs(run_id=1000)
        assert isinstance(jobs, list)
        assert len(jobs) > 0
        job_names = [j["name"] for j in jobs]
        assert "code-quality" in job_names
        assert "abap-validation" in job_names

    asyncio.run(run())


def test_mock_data_fallback_trigger_workflow(monkeypatch):
    """Verify trigger_workflow in mock mode appends a new run to mock runs and returns True."""

    async def run():
        monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
        service = GitHubService()

        success = await service.trigger_workflow(
            workflow_id="ci.yml", branch="feature/test-branch"
        )
        assert success is True

        runs = await service.get_workflow_runs(limit=30)
        assert any(r["branch"] == "feature/test-branch" for r in runs)

    asyncio.run(run())


def test_real_api_call_when_credentials_present_get_workflow_runs(monkeypatch):
    """Verify GitHubService attempts real HTTP API call when credentials are provided."""

    async def run():
        real_token = "ghp_1234567890abcdefghijklmn"
        monkeypatch.setattr(settings, "GITHUB_TOKEN", real_token)
        monkeypatch.setattr(settings, "GITHUB_REPO", "Rajiv6165/sapflow")

        service = GitHubService()
        assert service._is_mock_mode() is False

        mock_api_data = {
            "workflow_runs": [
                {
                    "id": 77777,
                    "name": "Real CI Run",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "abc1234",
                    "created_at": "2026-07-31T12:00:00Z",
                    "updated_at": "2026-07-31T12:05:00Z",
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = mock_api_data

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            runs = await service.get_workflow_runs(limit=10)

            # Assert actual HTTP GET call was made
            mock_get.assert_called_once()
            call_args, call_kwargs = mock_get.call_args
            assert (
                call_args[0]
                == "https://api.github.com/repos/Rajiv6165/sapflow/actions/runs"
            )
            assert call_kwargs["headers"]["Authorization"] == f"token {real_token}"
            assert call_kwargs["params"] == {"per_page": 10}

            # Assert returned data reflects API response
            assert len(runs) == 1
            assert runs[0]["id"] == 77777
            assert runs[0]["name"] == "Real CI Run"
            assert runs[0]["status"] == "success"

    asyncio.run(run())


def test_real_api_call_when_credentials_present_get_run_jobs(monkeypatch):
    """Verify GitHubService attempts real HTTP API call for run jobs when credentials are provided."""

    async def run():
        real_token = "ghp_1234567890abcdefghijklmn"
        monkeypatch.setattr(settings, "GITHUB_TOKEN", real_token)
        monkeypatch.setattr(settings, "GITHUB_REPO", "Rajiv6165/sapflow")

        service = GitHubService()

        mock_jobs_data = {
            "jobs": [
                {
                    "name": "build-job",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-07-31T12:00:00Z",
                    "completed_at": "2026-07-31T12:02:00Z",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "status": "completed",
                            "conclusion": "success",
                        }
                    ],
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = mock_jobs_data

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            jobs = await service.get_run_jobs(run_id=88888)

            mock_get.assert_called_once()
            call_args, call_kwargs = mock_get.call_args
            assert (
                call_args[0]
                == "https://api.github.com/repos/Rajiv6165/sapflow/actions/runs/88888/jobs"
            )
            assert call_kwargs["headers"]["Authorization"] == f"token {real_token}"

            assert len(jobs) == 1
            assert jobs[0]["name"] == "build-job"
            assert jobs[0]["status"] == "success"

    asyncio.run(run())


def test_real_api_call_when_credentials_present_trigger_workflow(monkeypatch):
    """Verify GitHubService attempts real HTTP POST call for workflow dispatches when credentials are provided."""

    async def run():
        real_token = "ghp_1234567890abcdefghijklmn"
        monkeypatch.setattr(settings, "GITHUB_TOKEN", real_token)
        monkeypatch.setattr(settings, "GITHUB_REPO", "Rajiv6165/sapflow")

        service = GitHubService()

        mock_response = MagicMock()
        mock_response.status_code = 204

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            success = await service.trigger_workflow(
                workflow_id="deploy.yml",
                branch="main",
                inputs={"environment": "production"},
            )

            assert success is True
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert (
                call_args[0]
                == "https://api.github.com/repos/Rajiv6165/sapflow/actions/workflows/deploy.yml/dispatches"
            )
            assert call_kwargs["headers"]["Authorization"] == f"token {real_token}"
            assert call_kwargs["json"] == {
                "ref": "main",
                "inputs": {"environment": "production"},
            }

    asyncio.run(run())


def test_real_api_call_failure_falls_back_to_mock_data(monkeypatch):
    """Verify that when real HTTP call fails (e.g. 500 or Exception), it logs error and falls back to mock data."""

    async def run():
        real_token = "ghp_1234567890abcdefghijklmn"
        monkeypatch.setattr(settings, "GITHUB_TOKEN", real_token)
        monkeypatch.setattr(settings, "GITHUB_REPO", "Rajiv6165/sapflow")

        service = GitHubService()

        with patch(
            "httpx.AsyncClient.get",
            side_effect=Exception("API limit exceeded or network down"),
        ):
            runs = await service.get_workflow_runs(limit=5)
            # Should fall back to mock runs when real API call raises an exception
            assert isinstance(runs, list)
            assert len(runs) > 0

    asyncio.run(run())

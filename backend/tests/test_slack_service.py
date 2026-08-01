import os
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.services.slack_service import SlackService


def test_slack_service_disabled_when_webhook_url_empty_or_placeholder():
    """Verify SlackService disabled state for empty, None, or placeholder webhook URLs."""
    urls_disabled = [
        None,
        "",
        "   ",
        "https://hooks.slack.com/services/placeholder",
        "https://hooks.slack.com/services/placeholder/xyz",
    ]
    for url in urls_disabled:
        service = SlackService(url)
        assert service.enabled is False


def test_slack_service_enabled_when_valid_webhook_url_configured():
    """Verify SlackService enabled state when valid webhook URL is provided."""
    valid_url = "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
    service = SlackService(valid_url)
    assert service.enabled is True


def test_slack_service_silently_noops_when_no_webhook_url_configured():
    """Verify SlackService methods return True, do not raise exceptions, and perform no network calls when no webhook URL is configured."""

    async def run():
        unconfigured_urls = [
            None,
            "",
            "   ",
            "https://hooks.slack.com/services/placeholder",
        ]
        for url in unconfigured_urls:
            service = SlackService(url)
            assert service.enabled is False

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                res_send = await service.send({"text": "test message"})
                res_pipeline = await service.notify_pipeline_result(
                    branch="main",
                    status="success",
                    duration=100,
                    run_url="https://github.com/run",
                    commit="commitsha",
                )
                res_promoted = await service.notify_transport_promoted(
                    transport_id="T101",
                    source="DEV",
                    target="QA",
                    promoted_by="user1",
                )
                res_rollback = await service.notify_transport_rollback(
                    transport_id="T101",
                    system="QA",
                )
                res_alert = await service.notify_system_alert(
                    alert_type="DiskFull",
                    message_text="Disk > 95%",
                    severity="critical",
                )

                # All calls should return True silently without raising exceptions
                assert res_send is True
                assert res_pipeline is True
                assert res_promoted is True
                assert res_rollback is True
                assert res_alert is True

                # Confirm no HTTP POST call was ever attempted
                mock_post.assert_not_called()

    asyncio.run(run())


def test_notify_pipeline_result_block_kit_formatting_success():
    """Verify Block Kit payload structure and green styling for successful pipeline completion."""

    async def run():
        webhook_url = (
            "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
        )
        service = SlackService(webhook_url)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            res = await service.notify_pipeline_result(
                branch="feature/sap-connect",
                status="success",
                duration=150,
                run_url="https://github.com/Rajiv6165/sapflow/actions/runs/99",
                commit="sha12345",
            )

            assert res is True
            mock_post.assert_called_once()

            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == webhook_url
            payload = call_kwargs["json"]

            assert payload["text"] == "SAPFlow CI Pipeline completed: SUCCESS"
            assert "attachments" in payload
            assert len(payload["attachments"]) == 1

            attachment = payload["attachments"][0]
            assert attachment["color"] == "#10b981"  # Success green

            blocks = attachment["blocks"]
            assert len(blocks) == 3

            # Section 1: Title & Emoji
            assert blocks[0]["type"] == "section"
            assert "*✅ SAPFlow CI Pipeline Result*" in blocks[0]["text"]["text"]

            # Section 2: Fields
            fields = blocks[1]["fields"]
            assert any("feature/sap-connect" in f["text"] for f in fields)
            assert any("SUCCESS" in f["text"] for f in fields)
            assert any("150s" in f["text"] for f in fields)
            assert any("`sha12345`" in f["text"] for f in fields)

            # Section 3: Action Button
            action_element = blocks[2]["elements"][0]
            assert action_element["type"] == "button"
            assert (
                action_element["url"]
                == "https://github.com/Rajiv6165/sapflow/actions/runs/99"
            )
            assert action_element["style"] == "primary"

    asyncio.run(run())


def test_notify_pipeline_result_block_kit_formatting_failure():
    """Verify Block Kit payload structure and red styling for failed pipeline completion."""

    async def run():
        webhook_url = (
            "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
        )
        service = SlackService(webhook_url)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            res = await service.notify_pipeline_result(
                branch="develop",
                status="failed",
                duration=45,
                run_url="https://github.com/Rajiv6165/sapflow/actions/runs/100",
                commit="err6789",
            )

            assert res is True
            mock_post.assert_called_once()

            payload = mock_post.call_args[1]["json"]
            assert payload["text"] == "SAPFlow CI Pipeline completed: FAILED"

            attachment = payload["attachments"][0]
            assert attachment["color"] == "#ef4444"  # Failure red

            blocks = attachment["blocks"]
            assert "*❌ SAPFlow CI Pipeline Result*" in blocks[0]["text"]["text"]

            action_element = blocks[2]["elements"][0]
            assert action_element["style"] == "danger"

    asyncio.run(run())


def test_notify_transport_promoted_payload_formatting():
    """Verify payload formatting for transport promotion notification."""

    async def run():
        webhook_url = (
            "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
        )
        service = SlackService(webhook_url)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            res = await service.notify_transport_promoted(
                "DEVK900123", "DEV", "QA", "admin_user"
            )

            assert res is True
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert "🚀 *Transport Promoted*" in payload["text"]
            assert "`DEVK900123`" in payload["text"]
            assert "DEV ➔ QA" in payload["text"]
            assert "admin_user" in payload["text"]

    asyncio.run(run())


def test_notify_transport_rollback_payload_formatting():
    """Verify payload formatting for transport rollback notification."""

    async def run():
        webhook_url = (
            "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
        )
        service = SlackService(webhook_url)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            res = await service.notify_transport_rollback("DEVK900123", "QA")

            assert res is True
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert "⚠️ *Transport Rollback Initiated*" in payload["text"]
            assert "`DEVK900123`" in payload["text"]
            assert "`QA`" in payload["text"]

    asyncio.run(run())


def test_notify_system_alert_color_coding():
    """Verify severity color coding for system health alerts (critical/warning/info)."""

    async def run():
        webhook_url = (
            "https://hooks.slack.com/services/TEST_TEAM/TEST_CHANNEL/TEST_HOOK_KEY"
        )
        service = SlackService(webhook_url)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Critical severity -> Red (#ef4444)
            await service.notify_system_alert("CPU Spike", "Usage > 95%", "CRITICAL")
            payload1 = mock_post.call_args_list[0][1]["json"]
            assert payload1["attachments"][0]["color"] == "#ef4444"

            # Warning severity -> Yellow (#f59e0b)
            await service.notify_system_alert("Memory High", "Usage > 80%", "WARNING")
            payload2 = mock_post.call_args_list[1][1]["json"]
            assert payload2["attachments"][0]["color"] == "#f59e0b"

            # Info severity -> Blue (#3b82f6)
            await service.notify_system_alert(
                "Service Restarted", "Normal operation", "INFO"
            )
            payload3 = mock_post.call_args_list[2][1]["json"]
            assert payload3["attachments"][0]["color"] == "#3b82f6"

    asyncio.run(run())

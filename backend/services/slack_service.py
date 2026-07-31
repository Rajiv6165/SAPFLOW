import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(
            webhook_url
            and "placeholder" not in webhook_url
            and webhook_url.strip() != ""
        )

    async def send(self, message: dict) -> bool:
        """Send a Slack message. Returns True on success, False if disabled or failed."""
        if not self.enabled:
            logger.info(
                f"[MOCK] Slack notification: {message.get('text') or message.get('attachments')}"
            )
            return True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url, json=message, timeout=5.0
                )
                if response.status_code != 200:
                    logger.warning(
                        f"Slack notification returned non-200 status: {response.status_code}"
                    )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Slack notification failed: {e}")
            return False

    async def notify_pipeline_result(
        self, branch: str, status: str, duration: int, run_url: str, commit: str = "N/A"
    ) -> bool:
        """Sends a rich Slack message using Block Kit attachments for pipeline status."""
        color = "#10b981" if status.lower() == "success" else "#ef4444"
        emoji = "✅" if status.lower() == "success" else "❌"

        message = {
            "text": f"SAPFlow CI Pipeline completed: {status.upper()}",
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{emoji} SAPFlow CI Pipeline Result*",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Branch:*\n{branch}"},
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Status:*\n{status.upper()}",
                                },
                                {"type": "mrkdwn", "text": f"*Duration:*\n{duration}s"},
                                {"type": "mrkdwn", "text": f"*Commit:*\n`{commit}`"},
                            ],
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Pipeline",
                                    },
                                    "url": run_url,
                                    "style": "primary"
                                    if status.lower() == "success"
                                    else "danger",
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        return await self.send(message)

    async def notify_transport_promoted(
        self, transport_id: str, source: str, target: str, promoted_by: str
    ) -> bool:
        """Sends notification with transport details and 🚀 emoji."""
        message = {
            "text": f"🚀 *Transport Promoted*\n*ID:* `{transport_id}`\n*Route:* {source} ➔ {target}\n*Promoted By:* {promoted_by}"
        }
        return await self.send(message)

    async def notify_transport_rollback(self, transport_id: str, system: str) -> bool:
        """Sends alert with ⚠️ emoji and rollback details."""
        message = {
            "text": f"⚠️ *Transport Rollback Initiated*\n*ID:* `{transport_id}`\n*System:* `{system}`"
        }
        return await self.send(message)

    async def notify_system_alert(
        self, alert_type: str, message_text: str, severity: str
    ) -> bool:
        """Sends CloudWatch alarm notification with severity color coding."""
        sev_lower = severity.lower()
        if "critical" in sev_lower or "high" in sev_lower:
            color = "#ef4444"  # Red
        elif "warning" in sev_lower or "medium" in sev_lower:
            color = "#f59e0b"  # Yellow/Orange
        else:
            color = "#3b82f6"  # Blue

        message = {
            "text": f"🚨 *System Health Alert:* {alert_type}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Alert Type:*\n{alert_type}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                        {"type": "mrkdwn", "text": f"*Detail:*\n{message_text}"},
                    ],
                }
            ],
        }
        return await self.send(message)

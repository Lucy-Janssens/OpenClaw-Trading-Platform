import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

async def notify(message: str) -> None:
    """Send a notification to a Discord webhook if configured."""
    webhook_url = settings.DISCORD_WEBHOOK_URL
    if not webhook_url:
        return

    payload = {"content": f"🦞 **OpenClaw** — {message}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload, timeout=5.0)
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Discord notification failed: {e}")

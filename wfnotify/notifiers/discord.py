"""Discord webhook notifier — posts a rich embed to a channel webhook."""

import logging
import time

import requests

from .base import Notifier, NotifierSendError

log = logging.getLogger(__name__)


def _inline(value: str) -> bool:
    return "\n" not in value and len(value) <= 30


class DiscordWebhookNotifier(Notifier):
    def __init__(self, webhook_url: str, timeout: float = 15.0):
        self.url = webhook_url
        self.timeout = timeout

    def send(self, title, body, fields, url=None, color=None) -> None:
        embed = {"title": (title or "")[:256], "footer": {"text": "warframe-notifier"}}
        if body:
            embed["description"] = body[:4096]
        if url:
            embed["url"] = url
        if color is not None:
            embed["color"] = color
        if fields:
            embed["fields"] = [
                {
                    "name": (str(name)[:256] or "​"),
                    "value": (str(val)[:1024] or "​"),
                    "inline": _inline(str(val)),
                }
                for name, val in fields[:25]
            ]
        payload = {"embeds": [embed]}

        for attempt in range(4):
            try:
                resp = requests.post(self.url, json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                raise NotifierSendError(f"discord POST error: {exc}") from exc

            if resp.status_code in (200, 204):
                return
            if resp.status_code == 429:
                retry_after = 1.0
                try:
                    retry_after = float(resp.json().get("retry_after", 1.0))
                except (ValueError, AttributeError):
                    pass
                log.warning("discord rate-limited (429); waiting %.1fs", retry_after)
                time.sleep(min(retry_after, 10))
                continue
            raise NotifierSendError(
                f"discord webhook returned {resp.status_code}: {resp.text[:200]}"
            )
        raise NotifierSendError("discord webhook gave up after repeated 429s")

"""Build the configured notifier instances; enforce that secrets exist for real channels."""

import logging

from .console import ConsoleNotifier
from .discord import DiscordWebhookNotifier

log = logging.getLogger(__name__)


class NotifierError(Exception):
    pass


def build_notifiers(cfg, dry_run: bool = False):
    """Return a list of Notifier instances. In dry_run, return a single ConsoleNotifier
    so the pipeline can run end-to-end without secrets or network."""
    if dry_run:
        return [ConsoleNotifier()]

    notifiers = []
    for ch in cfg.channels:
        if ch == "discord":
            url = cfg.secrets.get("discord_webhook_url")
            if not url:
                raise NotifierError(
                    "channel 'discord' is enabled but DISCORD_WEBHOOK_URL is empty in .env"
                )
            notifiers.append(DiscordWebhookNotifier(url, timeout=cfg.http.read_timeout))
        elif ch == "console":
            notifiers.append(ConsoleNotifier())
        elif ch == "telegram":
            raise NotifierError("telegram channel is not implemented yet")
        else:
            raise NotifierError(f"unknown channel: {ch}")

    if not notifiers:
        raise NotifierError("no notifiers configured")
    return notifiers

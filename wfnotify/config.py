"""Load and validate configuration from config.yaml + .env."""

import logging
import os
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv

log = logging.getLogger(__name__)

KNOWN_CHANNELS = {"discord", "telegram", "console"}


class ConfigError(Exception):
    pass


@dataclass
class HttpConfig:
    connect_timeout: float = 5.0
    read_timeout: float = 15.0
    retries: int = 3


@dataclass
class SourceConfig:
    name: str
    endpoint: str
    enabled: bool = True
    rules: dict = field(default_factory=dict)
    notify_on: list = field(default_factory=list)


@dataclass
class AppConfig:
    poll_interval_seconds: int
    language: str
    state_file: str
    log_file: str
    http: HttpConfig
    channels: list
    sources: list
    secrets: dict


def load_config(path: str = "config.yaml", env_path: str = ".env") -> AppConfig:
    load_dotenv(env_path)  # no-op if file missing

    if not os.path.exists(path):
        raise ConfigError(f"config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    http = HttpConfig(**(raw.get("http") or {}))

    sources = []
    for s in raw.get("sources", []) or []:
        if "name" not in s or "endpoint" not in s:
            raise ConfigError(f"source entry missing name/endpoint: {s!r}")
        sources.append(
            SourceConfig(
                name=s["name"],
                endpoint=s["endpoint"],
                enabled=s.get("enabled", True),
                rules=s.get("rules") or {},
                notify_on=s.get("notify_on") or [],
            )
        )

    secrets = {
        "discord_webhook_url": (os.getenv("DISCORD_WEBHOOK_URL") or "").strip(),
        "telegram_bot_token": (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip(),
        "telegram_chat_id": (os.getenv("TELEGRAM_CHAT_ID") or "").strip(),
    }

    cfg = AppConfig(
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 150)),
        language=raw.get("language", "en"),
        state_file=raw.get("state_file", "state.json"),
        log_file=raw.get("log_file", "notifier.log"),
        http=http,
        channels=list(raw.get("channels", ["discord"])),
        sources=sources,
        secrets=secrets,
    )
    _validate(cfg)
    return cfg


def _validate(cfg: AppConfig) -> None:
    if cfg.poll_interval_seconds < 120:
        log.warning(
            "poll_interval_seconds=%s is below the API's 120s cache; you'll just re-fetch stale data",
            cfg.poll_interval_seconds,
        )
    for ch in cfg.channels:
        if ch not in KNOWN_CHANNELS:
            raise ConfigError(f"unknown channel '{ch}' (known: {sorted(KNOWN_CHANNELS)})")
    if not cfg.sources:
        raise ConfigError("no sources configured")
    # Secret presence is enforced by the notifier registry (so --dry-run works without secrets).

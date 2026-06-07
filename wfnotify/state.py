"""Dedup state: which events we've already notified about, persisted atomically."""

import json
import logging
import os

from .timeutil import now_utc, parse_iso

log = logging.getLogger(__name__)


class StateStore:
    """Maps dedup_key -> event expiry (ISO string). Survives restarts; prunes expired keys."""

    def __init__(self, path: str, persist: bool = True):
        self.path = path
        self.persist = persist  # False for --dry-run: start empty, never write
        self.notified = {}
        self._dirty = False

    def load(self):
        if not self.persist or not os.path.exists(self.path):
            self.notified = {}
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.notified = dict(data.get("notified", {}))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            log.warning("state file %s unreadable (%s); starting empty", self.path, exc)
            self.notified = {}

    def seen(self, key: str) -> bool:
        return key in self.notified

    def mark(self, key: str, expiry) -> None:
        val = expiry.isoformat() if hasattr(expiry, "isoformat") else (str(expiry) if expiry else "")
        if self.notified.get(key) != val:
            self.notified[key] = val
            self._dirty = True

    def prune(self, now=None) -> int:
        """Drop entries whose expiry is in the past. Keep entries with unparseable/blank
        expiry (rare) to avoid accidentally re-notifying an event that's still active."""
        now = now or now_utc()
        drop = [k for k, exp in self.notified.items()
                if (dt := parse_iso(exp)) is not None and dt < now]
        for k in drop:
            del self.notified[k]
        if drop:
            self._dirty = True
        return len(drop)

    def save(self, force: bool = False) -> None:
        if not self.persist:
            return
        if not self._dirty and not force:
            return
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "notified": self.notified}, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)  # atomic on Windows + POSIX
        self._dirty = False

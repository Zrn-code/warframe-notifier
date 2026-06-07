"""Orchestration: for each source, fetch -> build_items -> diff against state -> notify -> persist."""

import logging

from .notifiers.base import NotifierSendError
from .timeutil import now_utc

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, http, sources, notifiers, state):
        self.http = http
        self.sources = sources
        self.notifiers = notifiers
        self.state = state

    def run_once(self, notify: bool = True) -> int:
        """One poll cycle across all sources. Returns the count of new items.

        notify=False ("seed" mode): mark all current matches as already-seen WITHOUT
        sending, so a later run only alerts on genuinely new events.
        """
        now = now_utc()
        total_new = 0

        for source in self.sources:
            try:
                raw = source.fetch(self.http)
            except Exception as exc:  # network/HTTP — log and keep other sources going
                log.warning("source %s: fetch failed: %s", source.name, exc)
                continue

            try:
                items = source.build_items(raw, now)
            except Exception:
                log.exception("source %s: build_items raised", source.name)
                continue

            new_items = [it for it in items if not self.state.seen(it.dedup_key)]
            log.info("source %s: %d match, %d new", source.name, len(items), len(new_items))

            for item in new_items:
                if not notify:
                    self.state.mark(item.dedup_key, item.expiry)
                    total_new += 1
                elif self._notify(item):
                    self.state.mark(item.dedup_key, item.expiry)
                    total_new += 1

        self.state.prune(now)
        self.state.save()
        return total_new

    def _notify(self, item) -> bool:
        """Send to every notifier. Returns True if at least one delivered (so we mark it seen)."""
        delivered = False
        for notifier in self.notifiers:
            try:
                notifier.send(item.title, item.body, item.fields, item.url, item.color)
                delivered = True
            except NotifierSendError as exc:
                log.warning("notifier %s failed for %s: %s", type(notifier).__name__, item.dedup_key, exc)
            except Exception:
                log.exception("notifier %s crashed for %s", type(notifier).__name__, item.dedup_key)
        return delivered

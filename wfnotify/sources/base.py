"""Source base class: fetch a worldstate endpoint, turn it into NotifyItems."""

from abc import ABC, abstractmethod


class Source(ABC):
    name = "base"

    def __init__(self, cfg):
        self.cfg = cfg            # SourceConfig
        self.name = cfg.name
        self.endpoint = cfg.endpoint
        self.rules = cfg.rules or {}

    def fetch(self, http):
        """Default: GET the endpoint. Returns parsed JSON (list/dict) or None if inactive."""
        return http.get_json(self.endpoint)

    @abstractmethod
    def build_items(self, raw, now):
        """Filter + render raw API data into a list[NotifyItem]. Already deduped by
        the caller via NotifyItem.dedup_key; sources only decide WHAT is worth notifying."""

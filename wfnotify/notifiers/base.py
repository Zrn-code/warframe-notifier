"""Common notifier interface."""

from abc import ABC, abstractmethod


class NotifierSendError(Exception):
    """Raised on a delivery failure so the pipeline does NOT mark the item as seen
    (it will be retried next cycle)."""


class Notifier(ABC):
    @abstractmethod
    def send(self, title, body, fields, url=None, color=None) -> None:
        """Deliver one notification. Raise NotifierSendError on failure."""

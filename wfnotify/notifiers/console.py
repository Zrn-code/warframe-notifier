"""Console notifier — prints to stdout. Used for --dry-run (no secrets, no network)."""

from .base import Notifier


class ConsoleNotifier(Notifier):
    def send(self, title, body, fields, url=None, color=None) -> None:
        print(f"\n=== {title} ===")
        if body:
            print(body)
        for name, val in fields:
            print(f"  {name}: {val}")
        if url:
            print(f"  -> {url}")

"""Shared data model passed from sources to notifiers."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class NotifyItem:
    """One thing worth telling the user about, already filtered and rendered.

    dedup_key  unique, stable key for this event/alert (prefixed by source name).
    expiry     when the underlying event ends — used to prune state once it's gone.
    fields     list of (name, value) shown as embed fields / lines.
    """

    dedup_key: str
    expiry: datetime
    title: str
    body: str = ""
    fields: List[Tuple[str, str]] = field(default_factory=list)
    url: Optional[str] = None
    color: Optional[int] = None

"""Source registry: maps config source names to their implementation classes."""

import logging

from .archonhunt import ArchonHuntSource
from .arbitration import ArbitrationSource
from .events import EventsSource
from .fissures import FissureSource
from .nightwave import NightwaveSource
from .sortie import SortieSource
from .voidtrader import VoidTraderSource

log = logging.getLogger(__name__)

SOURCE_REGISTRY = {
    "fissures": FissureSource,
    "voidTrader": VoidTraderSource,
    "sortie": SortieSource,
    "archonHunt": ArchonHuntSource,
    "arbitration": ArbitrationSource,
    "nightwave": NightwaveSource,
    "events": EventsSource,
}


def build_sources(cfg):
    sources = []
    for sc in cfg.sources:
        if not sc.enabled:
            continue
        cls = SOURCE_REGISTRY.get(sc.name)
        if cls is None:
            log.warning("unknown source '%s' in config; skipping", sc.name)
            continue
        sources.append(cls(sc))
    return sources

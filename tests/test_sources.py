import json
import os

from wfnotify.config import SourceConfig
from wfnotify.sources.arbitration import ArbitrationSource
from wfnotify.sources.fissures import FissureSource
from wfnotify.sources.nightwave import NightwaveSource
from wfnotify.sources.voidtrader import VoidTraderSource
from wfnotify.timeutil import now_utc

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _cfg(name, endpoint, rules=None, notify_on=None):
    return SourceConfig(name=name, endpoint=endpoint, rules=rules or {}, notify_on=notify_on or [])


def test_fissures_axi_only_matches_one():
    rules = {"tier_nums": [4], "steel_path": "no", "void_storm": "no"}
    src = FissureSource(_cfg("fissures", "/pc/fissures/", rules))
    items = src.build_items(_load("fissures.json"), now_utc())
    assert len(items) == 1
    assert items[0].dedup_key == "fissures:axi-survival-match"


def test_fissures_lith_only_matches_none():
    src = FissureSource(_cfg("fissures", "/pc/fissures/", {"tier_nums": [1], "steel_path": "no"}))
    # only the lith entry has tierNum 1, but the lith entry passes steel_path:no too -> 1 match
    items = src.build_items(_load("fissures.json"), now_utc())
    assert [i.dedup_key for i in items] == ["fissures:lith-tier-excluded"]


def test_arbitration_allowlist_and_expired():
    raw = _load("arbitration.json")
    # Defense is in the allow-list -> matches
    src = ArbitrationSource(_cfg("arbitration", "/pc/arbitration/",
                                 {"mission_type_keys": ["Survival", "Defense"], "min_minutes_left": 30}))
    assert len(src.build_items(raw, now_utc())) == 1

    # Spy not in allow-list -> filtered out
    src2 = ArbitrationSource(_cfg("arbitration", "/pc/arbitration/", {"mission_type_keys": ["Spy"]}))
    assert src2.build_items(raw, now_utc()) == []

    # expired -> never notify
    assert src.build_items({**raw, "expired": True}, now_utc()) == []


def test_nightwave_skips_dailies_by_default():
    src = NightwaveSource(_cfg("nightwave", "/pc/nightwave/", {"include_daily": False}))
    items = src.build_items(_load("nightwave.json"), now_utc())
    keys = {i.dedup_key for i in items}
    assert keys == {"nightwave:nw-weekly-1", "nightwave:nw-elite-1"}  # daily skipped

    elite = NightwaveSource(_cfg("nightwave", "/pc/nightwave/", {"elite_only": True}))
    items_e = elite.build_items(_load("nightwave.json"), now_utc())
    assert {i.dedup_key for i in items_e} == {"nightwave:nw-elite-1"}


def test_voidtrader_arriving():
    src = VoidTraderSource(_cfg("voidTrader", "/pc/voidTrader/", notify_on=["arriving", "here"]))
    items = src.build_items(_load("voidtrader_arriving.json"), now_utc())
    assert len(items) == 1
    assert items[0].dedup_key == "voidTrader:baro-visit-test:arriving"

from datetime import timedelta

from wfnotify.state import StateStore
from wfnotify.timeutil import now_utc


def test_mark_seen_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    s = StateStore(str(path))
    s.load()
    assert not s.seen("fissures:abc")
    s.mark("fissures:abc", now_utc() + timedelta(hours=1))
    assert s.seen("fissures:abc")
    s.save()

    s2 = StateStore(str(path))
    s2.load()
    assert s2.seen("fissures:abc")          # survives reload


def test_prune_drops_expired(tmp_path):
    s = StateStore(str(tmp_path / "state.json"))
    s.load()
    now = now_utc()
    s.mark("old", now - timedelta(hours=1))   # already expired
    s.mark("future", now + timedelta(hours=1))
    dropped = s.prune(now)
    assert dropped == 1
    assert not s.seen("old")
    assert s.seen("future")


def test_corrupt_state_starts_empty(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{ not valid json", encoding="utf-8")
    s = StateStore(str(path))
    s.load()
    assert s.notified == {}

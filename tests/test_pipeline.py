import json
import os

from wfnotify.config import SourceConfig
from wfnotify.pipeline import Pipeline
from wfnotify.sources.fissures import FissureSource
from wfnotify.state import StateStore

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


class FixtureHttp:
    def __init__(self, data):
        self.data = data

    def get_json(self, endpoint, params=None):
        return self.data


class RecordingNotifier:
    def __init__(self):
        self.sent = []

    def send(self, title, body, fields, url=None, color=None):
        self.sent.append(title)


def _fissure_pipeline(tmp_path):
    with open(os.path.join(FIX, "fissures.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = SourceConfig(name="fissures", endpoint="/pc/fissures/",
                       rules={"tier_nums": [4], "steel_path": "no", "void_storm": "no"})
    state = StateStore(str(tmp_path / "state.json"))
    state.load()
    notifier = RecordingNotifier()
    pipe = Pipeline(FixtureHttp(data), [FissureSource(cfg)], [notifier], state)
    return pipe, notifier


def test_dedup_does_not_resend(tmp_path):
    pipe, notifier = _fissure_pipeline(tmp_path)

    first = pipe.run_once()
    assert first == 1                 # one new Axi fissure
    assert len(notifier.sent) == 1

    second = pipe.run_once()
    assert second == 0                # already notified -> nothing new
    assert len(notifier.sent) == 1    # no extra send


def test_redelivers_after_state_cleared(tmp_path):
    pipe, notifier = _fissure_pipeline(tmp_path)
    pipe.run_once()
    pipe.state.notified.clear()       # simulate deleting the dedup entry
    pipe.state._dirty = True
    assert pipe.run_once() == 1       # notifies again
    assert len(notifier.sent) == 2

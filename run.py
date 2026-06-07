#!/usr/bin/env python
"""Warframe major-events notifier — CLI entrypoint.

Usage:
  python run.py --loop          # run forever (default); use this for the background service
  python run.py --once          # poll once and exit (Task Scheduler / cron friendly)
  python run.py --once --dry-run        # print what WOULD be sent; no secrets/network needed
  python run.py --notify-test           # send one test notification to verify the webhook
  python run.py --once --fixture f.json # feed a saved JSON response to all sources (testing)
"""

import argparse
import json
import logging
import sys
import time

from wfnotify.config import ConfigError, load_config
from wfnotify.http_client import HttpClient
from wfnotify.log import setup_logging
from wfnotify.notifiers.registry import NotifierError, build_notifiers
from wfnotify.pipeline import Pipeline
from wfnotify.sources import build_sources
from wfnotify.state import StateStore
from wfnotify.timeutil import discord_ts, now_utc

BASE_URL = "https://api.warframestat.us"


class FixtureHttp:
    """Stand-in HttpClient that returns the same parsed JSON for any endpoint.

    Sources' isinstance(list/dict) guards mean a fissures fixture only feeds the
    fissures source, a sortie fixture only the sortie source, etc."""

    def __init__(self, data):
        self.data = data

    def get_json(self, endpoint, params=None):
        return self.data


def build_pipeline(cfg, dry_run=False, fixture=None, persist=None):
    notifiers = build_notifiers(cfg, dry_run=dry_run)
    sources = build_sources(cfg)
    if persist is None:
        persist = not dry_run  # dry-run never writes state
    state = StateStore(cfg.state_file, persist=persist)
    state.load()
    if fixture is not None:
        with open(fixture, "r", encoding="utf-8") as f:
            http = FixtureHttp(json.load(f))
    else:
        http = HttpClient(BASE_URL, cfg.http, language=cfg.language)
    return Pipeline(http, sources, notifiers, state)


def cmd_notify_test(cfg):
    notifiers = build_notifiers(cfg, dry_run=False)
    for notifier in notifiers:
        notifier.send(
            title="✅ Warframe 通知器測試",
            body="看到這則訊息就代表通知管道設定成功，可以開始用了。",
            fields=[("狀態", "正常"), ("時間", discord_ts(now_utc()))],
            url="https://docs.warframestat.us/",
            color=0x2ECC71,
        )
    print("Test notification sent.")


def run_loop(pipeline, interval, log):
    log.info("loop started (interval=%ss). Press Ctrl+C to stop.", interval)
    while True:
        try:
            count = pipeline.run_once()
            log.info("cycle complete: %d new notification(s)", count)
        except Exception:
            log.exception("unexpected error during cycle; continuing")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            log.info("interrupted; saving state and exiting")
            pipeline.state.save(force=True)
            return


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warframe major-events notifier")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--env", default=".env")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--loop", action="store_true", help="run forever (default)")
    mode.add_argument("--once", action="store_true", help="poll once and exit")
    parser.add_argument("--dry-run", action="store_true", help="print instead of sending; no secrets needed")
    parser.add_argument("--notify-test", action="store_true", help="send one test notification and exit")
    parser.add_argument("--seed", action="store_true",
                        help="mark all currently-active events as seen WITHOUT notifying, so the "
                             "first real run is quiet (run this once right after setup)")
    parser.add_argument("--fixture", help="JSON file fed to all sources (for testing without live API)")
    args = parser.parse_args(argv)

    # Windows consoles default to a legacy codepage (e.g. cp936/GBK) that can't print
    # emoji or CJK; force UTF-8 so console + logging output never crashes.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # pythonw has no console streams

    try:
        cfg = load_config(args.config, args.env)
    except (ConfigError, OSError) as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    setup_logging(cfg.log_file)
    log = logging.getLogger("wfnotify")

    try:
        if args.notify_test:
            cmd_notify_test(cfg)
            return 0

        if args.seed:
            # dry_run=True -> no webhook needed; persist=True -> writes state; notify=False -> silent.
            pipeline = build_pipeline(cfg, dry_run=True, fixture=args.fixture, persist=True)
            count = pipeline.run_once(notify=False)
            log.info("seeded %d active event(s) as already-notified; future runs alert on NEW events only", count)
            print(f"Seeded {count} currently-active event(s). The notifier will now only alert on new ones.")
            return 0

        pipeline = build_pipeline(cfg, dry_run=args.dry_run, fixture=args.fixture)

        if args.once or args.fixture or args.dry_run:
            count = pipeline.run_once()
            log.info("done: %d new notification(s)", count)
            return 0

        run_loop(pipeline, cfg.poll_interval_seconds, log)
        return 0
    except NotifierError as exc:
        log.error("notifier setup error: %s", exc)
        print(f"notifier error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""Nightwave challenges. Notify per-challenge (dedup on challenge id). By default
skip dailies (too frequent) and notify weeklies/elites only."""

from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source


class NightwaveSource(Source):
    name = "nightwave"

    def build_items(self, raw, now):
        if not isinstance(raw, dict):
            return []
        include_daily = self.rules.get("include_daily", False)
        elite_only = self.rules.get("elite_only", False)
        season = raw.get("season")

        items = []
        for c in raw.get("activeChallenges") or []:
            if c.get("isDaily") and not include_daily:
                continue
            if elite_only and not c.get("isElite"):
                continue
            expiry = parse_iso(c.get("expiry"))
            if expiry is None or expiry < now:
                continue

            kind = "精英" if c.get("isElite") else ("每日" if c.get("isDaily") else "週常")
            title = c.get("title", "?")
            fields = [("類型", kind)]
            if c.get("reputation"):
                fields.append(("聲望", str(c["reputation"])))
            if season is not None:
                fields.append(("賽季", str(season)))
            fields.append(("結束", discord_ts(expiry)))

            items.append(
                NotifyItem(
                    dedup_key=f"nightwave:{c.get('id')}",
                    expiry=expiry,
                    title=f"🌙 夜光{kind}挑戰：{title}",
                    body=c.get("desc", ""),
                    fields=fields,
                    url="https://warframe.fandom.com/wiki/Nightwave",
                    color=0x1ABC9C,
                )
            )
        return items

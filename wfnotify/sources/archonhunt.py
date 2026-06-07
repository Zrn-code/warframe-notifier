"""Weekly Archon Hunt. id changes each week, so a new id => notify once."""

from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source


class ArchonHuntSource(Source):
    name = "archonHunt"

    def build_items(self, raw, now):
        if not isinstance(raw, dict):
            return []
        aid = raw.get("id")
        expiry = parse_iso(raw.get("expiry"))
        if not aid or expiry is None or expiry < now:
            return []

        boss = raw.get("boss", "?")
        faction = raw.get("faction", "")
        missions = raw.get("missions") or []
        mtypes = [m.get("type") or m.get("typeKey") or "?" for m in missions]

        fields = [("首領", str(boss))]
        if faction:
            fields.append(("陣營", str(faction)))
        if mtypes:
            fields.append(("任務序列", " → ".join(mtypes)))
        if raw.get("rewardPool"):
            fields.append(("獎勵池", str(raw["rewardPool"])))
        fields.append(("結束", discord_ts(expiry)))

        return [
            NotifyItem(
                dedup_key=f"archonHunt:{aid}",
                expiry=expiry,
                title="⚔️ 本週執政官狩獵 Archon Hunt",
                body=f"{boss}" + (f" · {faction}" if faction else ""),
                fields=fields,
                url="https://warframe.fandom.com/wiki/Archon_Hunt",
                color=0x8E44AD,
            )
        ]

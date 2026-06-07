"""Daily Sortie. id changes each day, so a new id => notify once."""

from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source


class SortieSource(Source):
    name = "sortie"

    def build_items(self, raw, now):
        if not isinstance(raw, dict):
            return []
        sid = raw.get("id")
        expiry = parse_iso(raw.get("expiry"))
        if not sid or expiry is None or expiry < now:
            return []

        boss = raw.get("boss", "?")
        faction = raw.get("faction", "")
        variants = raw.get("variants") or []

        fields = [("首領", str(boss))]
        if faction:
            fields.append(("陣營", str(faction)))
        for i, v in enumerate(variants[:3], 1):
            mtype = v.get("missionType") or v.get("missionTypeKey") or "?"
            modifier = v.get("modifierDescription") or v.get("modifier") or ""
            node = v.get("node") or ""
            value = "\n".join(x for x in (node, modifier) if x) or "—"
            fields.append((f"任務{i} · {mtype}", value))
        if raw.get("rewardPool"):
            fields.append(("獎勵池", str(raw["rewardPool"])))
        fields.append(("結束", discord_ts(expiry)))

        return [
            NotifyItem(
                dedup_key=f"sortie:{sid}",
                expiry=expiry,
                title="📋 今日突擊 Sortie",
                body=f"{boss}" + (f" · {faction}" if faction else ""),
                fields=fields,
                url="https://warframe.fandom.com/wiki/Sortie",
                color=0xC0392B,
            )
        ]

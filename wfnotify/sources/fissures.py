"""Void Fissures — the core source. Default config: Axi, non-Steel-Path, non-Storm."""

from ..filters import fissure_matches
from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source

AXI_COLOR = 0xE6B800  # gold


class FissureSource(Source):
    name = "fissures"

    def build_items(self, raw, now):
        items = []
        if not isinstance(raw, list):
            return items

        for f in raw:
            if not fissure_matches(f, self.rules):
                continue
            expiry = parse_iso(f.get("expiry"))
            if expiry is None or expiry < now:
                continue

            tier = f.get("tier", f.get("tierNum", "?"))
            mission = f.get("missionType") or f.get("missionTypeKey") or "?"
            node = f.get("node") or f.get("nodeKey") or "?"
            enemy = f.get("enemy") or f.get("enemyKey") or ""

            fields = [
                ("階級", str(tier)),
                ("任務", str(mission)),
                ("鋼鐵之路", "是" if f.get("isHard") else "否"),
            ]
            if f.get("isStorm"):
                fields.append(("虛空風暴", "是"))
            fields.append(("結束", discord_ts(expiry)))

            items.append(
                NotifyItem(
                    dedup_key=f"fissures:{f.get('id')}",
                    expiry=expiry,
                    title=f"新裂縫：{tier} · {mission}",
                    body=f"{node}" + (f" · {enemy}" if enemy else ""),
                    fields=fields,
                    url="https://warframe.fandom.com/wiki/Void_Fissure",
                    color=AXI_COLOR,
                )
            )
        return items

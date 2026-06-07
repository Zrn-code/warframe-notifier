"""Arbitration — rotates ~hourly (the noisiest source). Tame it with a mission-type
allow-list and a minimum-time-left guard. Dedup on id+expiry so each rotation fires once."""

from ..filters import in_allowlist
from ..models import NotifyItem
from ..timeutil import discord_ts, minutes_left, parse_iso
from .base import Source


def _human_node(raw):
    node = raw.get("node") or ""
    if not node or node.startswith("SolNode"):
        return raw.get("nodeKey") or node or "?"
    return node


class ArbitrationSource(Source):
    name = "arbitration"

    def build_items(self, raw, now):
        if not isinstance(raw, dict):
            return []
        if raw.get("expired") is True:
            return []

        expiry = parse_iso(raw.get("expiry"))
        if expiry is None or expiry < now:
            return []

        min_left = self.rules.get("min_minutes_left", 0)
        if minutes_left(expiry, now) < min_left:
            return []

        type_key = raw.get("typeKey") or raw.get("type")
        if not in_allowlist(type_key, self.rules.get("mission_type_keys")):
            return []
        enemy = raw.get("enemy")
        if not in_allowlist(enemy, self.rules.get("enemy_keys")):
            return []

        node = _human_node(raw)
        mtype = raw.get("type") or type_key or "?"
        fields = [("節點", str(node)), ("任務", str(mtype))]
        if enemy:
            fields.append(("敵人", str(enemy)))
        fields.append(("結束", discord_ts(expiry)))

        return [
            NotifyItem(
                dedup_key=f"arbitration:{raw.get('id', '')}:{raw.get('expiry', '')}",
                expiry=expiry,
                title=f"🎯 仲裁 Arbitration：{mtype}",
                body=f"{node}" + (f" · {enemy}" if enemy else ""),
                fields=fields,
                url="https://warframe.fandom.com/wiki/Arbitration",
                color=0xE67E22,
            )
        ]

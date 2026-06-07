"""Baro Ki'Teer (void trader): notify on arrival announcement and when he's actually here.

No `active` field exists — derive state from activation/expiry/inventory:
  arriving : activation > now (and inventory empty)
  here     : activation <= now <= expiry
  departed : now > expiry
"""

from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source


def _inventory_names(inventory, limit=6):
    names = []
    for it in inventory[:limit]:
        nm = it.get("item") or it.get("name") or it.get("uniqueName") or ""
        if nm:
            names.append(str(nm))
    return names


class VoidTraderSource(Source):
    name = "voidTrader"

    def build_items(self, raw, now):
        if not isinstance(raw, dict):
            return []

        vid = raw.get("id", "")
        location = raw.get("location") or "?"
        character = raw.get("character") or "Baro Ki'Teer"
        activation = parse_iso(raw.get("activation"))
        expiry = parse_iso(raw.get("expiry"))
        inventory = raw.get("inventory") or []
        notify_on = self.cfg.notify_on or ["arriving", "here"]
        url = "https://warframe.fandom.com/wiki/Baro_Ki%27Teer"

        if expiry is None or expiry < now:
            return []

        is_here = activation is not None and activation <= now <= expiry
        if is_here:
            if "here" not in notify_on:
                return []
            fields = [("地點", location), ("離場", discord_ts(expiry))]
            names = _inventory_names(inventory)
            if names:
                fields.append(("部分商品", "、".join(names)))
            return [
                NotifyItem(
                    dedup_key=f"voidTrader:{vid}:here",
                    expiry=expiry,
                    title=f"🛒 {character} 現身了！",
                    body=location,
                    fields=fields,
                    url=url,
                    color=0x2ECC71,
                )
            ]

        # arriving (activation in the future)
        if "arriving" in notify_on and activation is not None and activation > now:
            return [
                NotifyItem(
                    dedup_key=f"voidTrader:{vid}:arriving",
                    expiry=expiry,  # keep until he leaves so it doesn't re-fire
                    title=f"⏳ {character} 即將造訪",
                    body=location,
                    fields=[
                        ("地點", location),
                        ("抵達", discord_ts(activation)),
                        ("離場", discord_ts(expiry)),
                    ],
                    url=url,
                    color=0x3498DB,
                )
            ]
        return []

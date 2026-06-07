"""Limited-time events / operations. Response is an ARRAY; dedup per event id."""

from ..models import NotifyItem
from ..timeutil import discord_ts, parse_iso
from .base import Source


class EventsSource(Source):
    name = "events"

    def build_items(self, raw, now):
        items = []
        if not isinstance(raw, list):
            return items

        for e in raw:
            expiry = parse_iso(e.get("expiry"))
            if expiry is None or expiry < now:
                continue
            desc = e.get("description") or "限時活動"
            faction = e.get("faction") or ""
            node = e.get("node") or ""

            fields = []
            if faction:
                fields.append(("陣營", str(faction)))
            if node:
                fields.append(("地點", str(node)))
            fields.append(("結束", discord_ts(expiry)))

            items.append(
                NotifyItem(
                    dedup_key=f"events:{e.get('id')}",
                    expiry=expiry,
                    title=f"🎉 限時活動：{desc}",
                    body=e.get("tooltip", "") or "",
                    fields=fields,
                    url="https://warframe.fandom.com/wiki/Events",
                    color=0xF1C40F,
                )
            )
        return items

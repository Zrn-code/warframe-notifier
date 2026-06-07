"""Time helpers: parse the API's ISO8601 timestamps and render Discord timestamps."""

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Current time as a tz-aware UTC datetime."""
    return datetime.now(timezone.utc)


def parse_iso(value):
    """Parse an ISO8601 string (e.g. "2026-06-07T14:09:54.689Z") to a tz-aware UTC datetime.

    Returns None on missing/blank input or unparseable values — notably the API's
    out-of-range placeholder expiry "+275760-09-13T00:00:00.000Z" used for inactive
    arbitration, which exceeds datetime's max year and must be treated as "no time".
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def discord_ts(dt: datetime, style: str = "R") -> str:
    """Render a Discord dynamic timestamp tag.

    style "R" -> relative ("in 24 minutes"); "f" -> short date/time. Discord renders
    these live in each viewer's local timezone.
    """
    return f"<t:{int(dt.timestamp())}:{style}>"


def minutes_left(dt: datetime, ref: datetime = None) -> float:
    """Whole/fractional minutes from ref (default now) until dt. Negative if past."""
    ref = ref or now_utc()
    return (dt - ref).total_seconds() / 60.0

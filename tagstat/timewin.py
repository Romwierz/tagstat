"""Parsing of verbal time windows like 'last 10 min' into timestamps.

The window is expressed as offsets "ago" relative to a reference `now`:
both --since and --until count backwards (e.g. --until 'last 1 hour' means
"up to one hour ago"). When a bound is omitted it defaults to the data range
(oldest sample for since, newest for until).
"""
from __future__ import annotations
import re

# unit alias -> seconds
_UNITS = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
}

# optional leading "last", a number, then a unit; e.g. "last 10 min", "1.5h", "90 s"
_PATTERN = re.compile(r"^\s*(?:last\s+)?(\d+(?:\.\d+)?)\s*([a-z]+)\s*$", re.I)


def parse_duration(text: str) -> float:
    """Parse a verbal duration ('last 10 min', '1.5 h', '90s') into seconds."""
    m = _PATTERN.match(text)
    if not m:
        raise ValueError(f"Cannot parse duration: {text!r}")
    value, unit = float(m.group(1)), m.group(2).lower()
    if unit not in _UNITS:
        raise ValueError(f"Unknown time unit: {unit!r}")
    return value * _UNITS[unit]


def resolve_window(since: str | None, until: str | None, *, now: float,
                   data_min: float | None = None,
                   data_max: float | None = None) -> tuple[float | None, float | None]:
    """Resolve verbal since/until bounds into absolute timestamps.

    A given bound is interpreted as "that long ago" (now - duration).
    An omitted bound falls back to the data range edge.
    """
    s = now - parse_duration(since) if since else data_min
    u = now - parse_duration(until) if until else data_max
    return s, u


if __name__ == "__main__":
    # python -m tagstat.timewin
    now = 1_000_000.0
    for txt in ["last 10 min", "1.5 h", "90s", "2 hours"]:
        print(f"{txt:12} -> {parse_duration(txt):>8.0f} s")
    print("window (since='last 2 hr', until='last 1 hour'):",
          resolve_window("last 2 hr", "last 1 hour", now=now))
    print("window (defaults to data range):",
          resolve_window(None, None, now=now, data_min=100.0, data_max=200.0))

"""Snapshot rendering of per-tag RTLS stats as a rich table.

This is the central display layer: a plain, importable function usable from a
REPL, the CLI, or (later) an API. It selects tags (exact list / substring /
regex), computes stats over a resolved time window, sorts by stability, keeps
the top N, and renders a readable table.

All position values are in meters.
"""
from __future__ import annotations
import re
import time
from .stats import compute_stats, TagStats
from . import timewin

Point = tuple[float, float]

# sort key -> how to score a TagStats (always sorted descending: worst first)
_SORT_KEYS = {
    "rms": lambda s: s.rms,
    "std": lambda s: max(s.std),
    "error": lambda s: (s.error if s.error is not None else -1.0),
    "count": lambda s: s.count,
}


def _select_tags(store, tags=None, pattern=None, regex=False) -> list[str]:
    """Pick tag ids: explicit list, else substring/regex match, else all."""
    all_tags = store.tag_ids()
    if tags:
        wanted = set(tags)
        return [t for t in all_tags if t in wanted]
    if pattern:
        if regex:
            rx = re.compile(pattern)
            return [t for t in all_tags if rx.search(t)]
        return [t for t in all_tags if pattern in t]
    return all_tags


def collect_stats(store, *, tags=None, pattern=None, regex=False,
                  since=None, until=None, now=None, refs=None,
                  exclude_moving=False, moving_threshold=0.5,
                  sort_by="rms", top=None) -> list[TagStats]:
    """Compute stats for the selected tags over the resolved time window."""
    now = time.time() if now is None else now
    refs = refs or {}

    results: list[TagStats] = []
    for tag in _select_tags(store, tags, pattern, regex):
        data = store.query(tag)
        if not data:
            continue
        # resolve the window against this tag's own data range when a bound is omitted
        s, u = timewin.resolve_window(since, until, now=now,
                                      data_min=data[0].ts, data_max=data[-1].ts)
        st = compute_stats(tag, store.query(tag, since=s, until=u), ref=refs.get(tag))
        if st.count == 0:
            continue
        if exclude_moving and st.moving_fraction >= moving_threshold:
            continue
        results.append(st)

    results.sort(key=_SORT_KEYS.get(sort_by, _SORT_KEYS["rms"]), reverse=True)
    return results[:top] if top is not None else results


def build_table(stats: list[TagStats], *, rms_warn: float = 0.10, title=None):
    """Build a rich Table from a list of TagStats (rms above rms_warn shown red)."""
    from rich.table import Table

    table = Table(title=title, header_style="bold")
    for col in ("tag", "n", "rate", "mean (x,y)", "std x", "std y",
                "rms", "error", "moving"):
        table.add_column(col, justify="left" if col == "tag" else "right")

    for s in stats:
        span = (s.t_end - s.t_start) if (s.t_end and s.t_start) else 0.0
        rate = (s.count - 1) / span if span > 0 else 0.0
        rms = f"{s.rms:.3f}"
        rms_cell = f"[red]{rms}[/red]" if s.rms >= rms_warn else f"[green]{rms}[/green]"
        err = f"{s.error:.3f}" if s.error is not None else "-"
        table.add_row(
            s.tag_id, str(s.count), f"{rate:.1f}Hz",
            f"({s.mean[0]:.2f},{s.mean[1]:.2f})",
            f"{s.std[0]:.3f}", f"{s.std[1]:.3f}",
            rms_cell, err, f"{s.moving_fraction:.0%}",
        )
    return table


def render(store, *, console=None, title=None, **kwargs):
    """Convenience: compute stats and print the table once. Returns the stats."""
    from rich.console import Console

    stats = collect_stats(store, **kwargs)
    table = build_table(stats, title=title or "tagstat — RTLS stability (meters)")
    (console or Console()).print(table)
    return stats


if __name__ == "__main__":
    # python -m tagstat.render
    from .model import Sample
    from .store import MemoryStore

    st = MemoryStore()
    # stable tag: tight cluster around (10, 5)
    for i, (dx, dy) in enumerate([(0.01, -0.01), (-0.02, 0.01),
                                  (0.0, 0.02), (-0.01, -0.01)]):
        st.add(Sample("tag-stable", 10 + dx, 5 + dy, ts=1000 + i))
    # noisy tag: same center, wide spread
    for i, (dx, dy) in enumerate([(0.5, -0.4), (-0.6, 0.3),
                                  (0.2, 0.7), (-0.3, -0.5)]):
        st.add(Sample("tag-noisy", 10 + dx, 5 + dy, ts=1000 + i))
    # moving tag: drifting, flagged is_moving
    for i in range(4):
        st.add(Sample("tag-moving", 20 + i, 30 + 2 * i, ts=1000 + i, is_moving=True))

    render(st, refs={"tag-stable": (10.0, 5.0)}, sort_by="rms")

"""Interactive REPL console for tagstat.

Launches a background MQTT collector and lets you display per-tag stability
tables on demand. The intro explains the main action (show a table for a tag);
`help` lists every command and `help <cmd>` shows its usage.
"""
from __future__ import annotations
import cmd
import sys
import time
from .collector import Collector
from .render import collect_stats, build_table

INTRO = """\
tagstat REPL — RTLS data stability monitor (values in meters)

Collecting live data in the background. Main commands:
  show <tag>     display the stats table for a tag, e.g.  show 45306
  watch <tag>    live table that refreshes as new data arrives (Ctrl-C to stop)
  show           show all tags (sorted by worst stability)

Other: since <window> | sort <key> | top <n> | exclude on|off |
       ref <tag> <x> <y> | interval <sec> | tags | status | help | quit
"""


class TagstatRepl(cmd.Cmd):
    prompt = "tagstat> "
    intro = INTRO

    def __init__(self, collector: Collector):
        super().__init__()
        self.collector = collector
        # display state, applied by every `show`
        self.since: str | None = None
        self.sort_by = "rms"
        self.top: int | None = None
        self.exclude_moving = False
        self.interval = 1.0   # watch refresh period, seconds
        self.refs: dict[str, tuple[float, float]] = {}

        from rich.console import Console
        self.console = Console()

    def _build(self, pattern):
        """Build the rich table for the current display settings."""
        stats = collect_stats(self.collector.store, pattern=pattern, since=self.since,
                              sort_by=self.sort_by, top=self.top,
                              exclude_moving=self.exclude_moving, refs=self.refs)
        title = (f"tagstat — {pattern or 'all tags'} (meters) | "
                 f"recv(all)={self.collector.received}")
        return build_table(stats, title=title)

    # --- main action --------------------------------------------------------
    def do_show(self, arg):
        """show [TAG] — display the stats table; TAG filters by substring (omit = all tags)."""
        self.console.print(self._build(arg.strip() or None))

    def do_watch(self, arg):
        """watch [TAG] — live table refreshing as new data arrives; Ctrl-C to stop."""
        from rich.live import Live
        pattern = arg.strip() or None
        try:
            with Live(self._build(pattern), console=self.console,
                      refresh_per_second=4) as live:
                while True:
                    time.sleep(self.interval)
                    live.update(self._build(pattern))
        except KeyboardInterrupt:
            self.console.print("[dim](stopped)[/dim]")

    def do_interval(self, arg):
        """interval SEC — set the watch refresh period in seconds (default 1.0)."""
        try:
            self.interval = float(arg)
            print(f"interval = {self.interval}s")
        except ValueError:
            print("usage: interval SEC")

    # --- display settings ---------------------------------------------------
    def do_since(self, arg):
        """since [WINDOW] — set the time window, e.g. 'last 10 min'; empty = full range."""
        self.since = arg.strip() or None
        print(f"since = {self.since!r}")

    def do_sort(self, arg):
        """sort KEY — sort rows by rms | std | error | count (worst first)."""
        key = arg.strip()
        if key not in ("rms", "std", "error", "count"):
            print("key must be one of: rms, std, error, count")
            return
        self.sort_by = key
        print(f"sort_by = {key}")

    def do_top(self, arg):
        """top [N] — keep only the N worst tags; empty = no limit."""
        self.top = int(arg) if arg.strip() else None
        print(f"top = {self.top}")

    def do_exclude(self, arg):
        """exclude on|off — hide tags the system reports as moving."""
        self.exclude_moving = arg.strip().lower() in ("on", "true", "1", "yes")
        print(f"exclude_moving = {self.exclude_moving}")

    def do_ref(self, arg):
        """ref TAG X Y — set a known reference position for a tag (enables the error column)."""
        try:
            tag, x, y = arg.split()
            self.refs[tag] = (float(x), float(y))
            print(f"ref[{tag}] = ({x}, {y})")
        except ValueError:
            print("usage: ref TAG X Y")

    # --- info ---------------------------------------------------------------
    def do_tags(self, arg):
        """tags — list tag ids seen so far."""
        ids = self.collector.store.tag_ids()
        print(", ".join(sorted(ids)) if ids else "(no tags yet)")

    def do_status(self, arg):
        """status — collector connection and message counters."""
        c = self.collector
        print(f"broker={c.broker}:{c.port} topic={c.topic} "
              f"received={c.received} errors={c.errors} "
              f"tags={len(c.store.tag_ids())}")

    # --- exit ---------------------------------------------------------------
    def do_quit(self, arg):
        """quit — exit the REPL."""
        return True

    do_EOF = do_quit  # Ctrl-D exits too

    def emptyline(self):
        pass  # blank line does nothing (default would repeat last command)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    broker = argv[0] if argv else "192.168.2.145"

    collector = Collector(broker=broker).start()
    try:
        TagstatRepl(collector).cmdloop()
    except KeyboardInterrupt:
        print()  # clean newline after Ctrl-C
    finally:
        collector.stop()

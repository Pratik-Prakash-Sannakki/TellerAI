"""Tool result prefixes meaning "that did not work" (discovery.py 1092-1093).

Its own module, importing nothing: the recorder reads it, and ``guard.py`` (which re-exports it)
imports the run, which imports the recorder.
"""

from __future__ import annotations

FAILED = (
    "NO CHANGE",
    "NOTHING TYPED",
    "TYPED at",
    "STALE",
    "OUT OF VIEW",
    "REFUSED",
    "NOT YET",
    "LOOK FIRST",
    "BAD TARGET",
    "SKIP",
    "HTTP ERROR",
)
"""Tool result prefixes meaning "that did not work"."""

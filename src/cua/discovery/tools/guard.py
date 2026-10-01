"""Tool guards. Step 3 holds only ``FAILED``; later steps add the lock and step budget."""

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

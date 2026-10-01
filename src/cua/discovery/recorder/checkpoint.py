"""The capability's checkpoint: the text replay must see to call the run a success.

Moved unchanged from notebooks/discovery/discovery.py (``checkpoint``).
"""

from __future__ import annotations

from cua.discovery.recorder.events import READ_TOOLS
from cua.safety.redact import norm
from cua.schema import Event


def checkpoint(log: list[Event], fallback: str) -> str:
    """C: after a send, the page's own response proves success (the agent's proof only if it is
    part of that response). A read-only run: text seen on the page of the last read (the agent's
    page heading, else its proof, else the value's label, else a word on it), never text the start
    page also shows (after logout the proof is the login page) or text on half the run's looks (a
    footer). Otherwise the proof, else the model's text."""
    proof = [ev["args"]["proof_text"] for ev in log if ev["tool"] == "finish_business_outcome"]
    response = next((ev["landed"] for ev in reversed(log) if ev.get("landed")), [])
    if response:
        return next(  # type: ignore[return-value]
            (p for p in reversed(proof) if any(norm(p) in norm(t) for t in response)), response[0]  # type: ignore[arg-type,index,union-attr]
        )
    read = next((ev for ev in reversed(log) if ev["tool"] in READ_TOOLS), None)
    if read:
        start = next((ev for ev in log if ev["tool"] == "start"), {})  # type: ignore[var-annotated]
        common = {
            t for t, n in start.get("text_counts", {}).items() if n >= start.get("looks", 0) / 2  # type: ignore[operator]
        }
        chrome = common | {norm(t) for t in start.get("start_texts", [])}
        on_page = {norm(t) for t in read.get("page_texts", [])}
        picks = [
            *read.get("headings", []),
            *reversed(proof),
            read.get("label"),
            *read.get("page_texts", []),
        ]
        if pick := next(
            (p for p in picks if p and norm(p) in on_page and norm(p) not in chrome), None  # type: ignore[arg-type]
        ):
            return pick  # type: ignore[return-value]
    return proof[-1] if proof else fallback  # type: ignore[return-value]

"""The capability's checkpoint: the text replay must see to call the run a success.

It names the final screen and stays the same between runs: never a value (a digit: an amount, a
date, an id; or a run value), never a lone form label ('City:') or a single word ('Account'), never
a link bar ('Home | About Us I Services'). Text new on the final screen is preferred over text an
earlier screen also showed (a menu). "Seen before" is OCR-tolerant: OCR reads a '|' separator as
'I', 'l' or '1' from one look to the next, so those count as the same text (``_key``).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Collection

from cua.discovery.recorder.events import READ_TOOLS
from cua.safety.redact import norm, redactor
from cua.schema import Event

WARNING = "checkpoint: no stable final-screen text; kept a text that may change between runs"


def stable(values: Collection[str] = ()) -> Callable[[str | None], bool]:
    """text -> True when it could be a checkpoint: no digit, no run value, not a form label or a
    label with its value (':', '#' or '$' in it: 'City:', 'Amount: $', 'Account Type: CHECKING'),
    not a link bar, and two words or more."""
    redact = redactor(set(values))
    return lambda t: bool(
        t
        and not re.search(r"[\d:#$]", t)
        and not _link_bar(t)
        and redact(t) == t
        and len(_words(t)) >= 2  # noqa: PLR2004
    )


def _link_bar(text: str) -> bool:
    """A '|' anywhere, or two OCR-read separators ('Home I About Us I Services'): a site's link
    bar (menu or footer), on every page, so it names no screen."""
    return "|" in text or len(_SEP.findall(text)) >= 2  # noqa: PLR2004


_SEP = re.compile(r"(?:^|(?<=\s))[Il1](?=\s|$)")


def _key(text: str | None) -> str:
    """``norm`` with every separator OCR may read for '|' ('I', 'l', '1', alone) as '|'."""
    spaced = re.sub(r"\s*\|\s*", " | ", norm(text))
    return " ".join("|" if w in {"|", "i", "l", "1"} else w for w in spaced.split())


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", text.casefold())


def checkpoint(log: list[Event], fallback: str, values: Collection[str] = ()) -> str:
    """C: after a send, the page's own response proves success (the agent's proof first, if it is
    part of that response). A read-only run: text seen on the page of the last read, never text
    the start page also shows (after logout the proof is the login page), new on that screen (not
    inside an earlier screen's text, and a word no earlier screen had): text on under half the
    run's looks first (not the menu or footer), then more new words (a heading or sentence, not a
    link), then fewer looks, then longer, then the agent's heading, proof, the value's label, a
    word on it. Otherwise the proof, else the model's text. Every pick must be ``stable``; with
    none new, the best stable text, else the old pick, is kept and a warning logged."""
    ok = stable(values)
    proof = [ev["args"]["proof_text"] for ev in log if ev["tool"] == "finish_business_outcome"]
    response: list[str] = next((ev["landed"] for ev in reversed(log) if ev.get("landed")), [])  # type: ignore[misc]
    if response:
        picks = [p for p in reversed(proof) if any(norm(p) in norm(t) for t in response)]  # type: ignore[arg-type]
        return _pick(log, [*picks, *response], ok)  # type: ignore[list-item]
    at = next((i for i in reversed(range(len(log))) if log[i]["tool"] in READ_TOOLS), None)
    if at is not None and (cands := _on_page(log, at, proof)):  # type: ignore[arg-type]
        start = next((ev for ev in log if ev["tool"] == "start"), {})  # type: ignore[var-annotated]
        counts: Counter[str] = Counter()
        for t, n in start.get("text_counts", {}).items():
            counts[_key(t)] += n
        half = start.get("looks", 0) / 2  # type: ignore[operator]
        earlier = [_key(t) for ev in log[:at] for t in ev.get("from_texts", [])]
        seen = {w for t in [*earlier, *map(_key, start.get("start_texts", []))] for w in _words(t)}

        def new(p: str) -> int:
            k = _key(p)
            return 0 if any(k in e for e in earlier) else len(set(_words(k)) - seen)

        def rank(p: str) -> tuple[bool, int, int, int]:
            n = counts.get(_key(p), 0)
            return n >= half > 0, -new(p), n, -len(_words(p))

        good = sorted((p for p in cands if ok(p)), key=rank)
        if good and new(good[0]):
            return good[0]
        common = {t for t, n in counts.items() if n >= half}
        if old := good[0] if good else next((p for p in cands if _key(p) not in common), None):
            return _warn(log, old)
    return _pick(log, [*reversed(proof), fallback], ok)  # type: ignore[list-item]


def _on_page(log: list[Event], at: int, proof: list[str]) -> list[str]:
    """The read's candidates, in order, that its page shows and the start page does not (OCR-
    tolerant: a variant of a start-page text is the start page's text)."""
    read = log[at]
    start: Event | dict[str, list[str]] = next((ev for ev in log if ev["tool"] == "start"), {})
    chrome = {_key(t) for t in start.get("start_texts", [])}
    on_page = {norm(t) for t in read.get("page_texts", [])}
    picks = [
        *read.get("headings", []),
        *reversed(proof),
        read.get("label"),
        *read.get("page_texts", []),
    ]
    return [p for p in picks if p and norm(p) in on_page and _key(p) not in chrome]


def _pick(log: list[Event], picks: list[str], ok: Callable[[str | None], bool]) -> str:
    """The first stable pick, else the first (the old rule) with a warning."""
    return next((p for p in picks if ok(p)), None) or _warn(log, picks[0])


def _warn(log: list[Event], text: str) -> str:
    """Log once that the checkpoint may change between runs. Never the text itself."""
    if not any(ev["tool"] == "warning" and ev["result"] == WARNING for ev in log):
        warning: Event = {
            "tool": "warning",
            "args": {},
            "result": WARNING,
            "point": None,
            "url": "",
            "crop": None,
        }
        log.append(warning)
    return text

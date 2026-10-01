"""Value masking: ``norm`` (compare texts) and ``redactor`` (mask this run's values in a text).

Moved unchanged from notebooks/discovery/discovery.py (the discovery versions: ``NUMBER`` without
look-arounds, ``redactor`` with ``mask=``). Replay's own variant differs and stays separate.
"""

from __future__ import annotations

import re
from collections.abc import Callable

NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?")


def _num(text: str) -> str:
    n = text.lstrip("$").replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def redactor(values: set[str], mask: str = "***") -> Callable[[str], str]:
    """text -> text with every value masked. Numbers match however they are written
    ('100000' = '$100,000.00'); words match whole, case-insensitively ('IL' never hits 'Bill')."""
    nums = {_num(v) for v in values if NUMBER.fullmatch(v.strip())}
    words = sorted(
        (v for v in values if len(v.strip()) > 1 and not NUMBER.fullmatch(v.strip())),
        key=len,
        reverse=True,
    )
    word_re = (
        re.compile("|".join(rf"(?<!\w){re.escape(w.strip())}(?!\w)" for w in words), re.I)
        if words
        else None
    )

    def redact(text: str) -> str:
        text = NUMBER.sub(lambda m: mask if _num(m.group()) in nums else m.group(), text)
        return word_re.sub(mask, text) if word_re else text

    return redact


def norm(text: str | None) -> str:
    return " ".join((text or "").casefold().split()).rstrip(".:!?").strip()

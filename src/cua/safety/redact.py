"""Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``, ``mask_png``.

Moved unchanged from the notebooks. ``redactor`` is discovery's (with ``mask=``); replay's own
variant differs only in its number pattern -- whole numbers only, never the '1' in 'rung1' -- so it
is ``REPLAY_NUMBER``, passed as ``redactor(values, number=REPLAY_NUMBER)``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping

import numpy as np
from numpy.typing import NDArray

from cua.vision.look import Box, decode, encode

NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?")  # discovery
REPLAY_NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?(?!\w)")  # whole numbers only

OcrFn = Callable[[NDArray[np.uint8]], list[tuple[str, Box]]]


def _num(text: str) -> str:
    n = text.lstrip("$").replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def redactor(
    values: set[str], mask: str = "***", number: re.Pattern[str] = NUMBER
) -> Callable[[str], str]:
    """text -> text with every value masked. Numbers match however they are written
    ('100000' = '$100,000.00'); words match whole, case-insensitively ('IL' never hits 'Bill')."""
    nums = {_num(v) for v in values if number.fullmatch(v.strip())}
    words = sorted(
        (v for v in values if len(v.strip()) > 1 and not number.fullmatch(v.strip())),
        key=len,
        reverse=True,
    )
    word_re = (
        re.compile("|".join(rf"(?<!\w){re.escape(w.strip())}(?!\w)" for w in words), re.I)
        if words
        else None
    )

    def redact(text: str) -> str:
        text = number.sub(lambda m: mask if _num(m.group()) in nums else m.group(), text)
        return word_re.sub(mask, text) if word_re else text

    return redact


def norm(text: str | None) -> str:
    return " ".join((text or "").casefold().split()).rstrip(".:!?").strip()


def is_sensitive(label: str, sensitive_words: Iterable[str]) -> bool:
    return any(w in label.casefold() for w in sensitive_words)


def hide_secrets(text: str, secrets: Mapping[str, str]) -> str:
    """Each secret value -> ``<name>``. ``secrets`` maps a secret NAME to its value."""
    for name, value in secrets.items():
        if value:
            text = text.replace(value, f"<{name}>")
    return text


def mask_png(png: bytes, redact: Callable[[str], str], ocr_fn: OcrFn) -> bytes:
    """Black out every OCR box whose text holds a run value. A clean image is written as is.
    ``ocr_fn`` is the caller's OCR (e.g. ``lambda img: ocr(img, cfg.ocr_min_score)``)."""
    img = decode(png)
    hits = [box for text, box in ocr_fn(img) if redact(text) != text]
    for b in hits:
        img[b.y1 : b.y2, b.x1 : b.x2] = 0
    return encode(img) if hits else png

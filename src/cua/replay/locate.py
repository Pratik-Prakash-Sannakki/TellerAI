"""Locating a target on screen: the rungs. Rung 1 the target's own OCR text, rung 2 a label +
offset, rung 3 a template crop, or a table cell. Never raw x, y.

Moved unchanged from notebooks/replay/replay.py (``same_text``, ``typed_ok``, ``same_label``,
``find_text``, ``find_template``, ``read_cell``, ``anchor_point``, ``text_hit``, ``locate``,
865-951). ``CFG.fuzzy``/``template_threshold``/``template_margin``/``near_px`` become a
``cfg: ReplayConfig`` parameter, threaded through rather than read off a global. ``find`` (954,
async, scrolls the page) is not in this step.
"""

from __future__ import annotations

import difflib
import math
import re
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from cua.config import ReplayConfig
from cua.replay.loader import fill
from cua.safety.redact import norm
from cua.schema import Anchor, OcrText, TableCell, Target
from cua.vision import Element, Look, decode

SameTextLike = Callable[[str, str, ReplayConfig], bool]


def same_text(seen: str, want: str, cfg: ReplayConfig) -> bool:
    """Exact for anything with a digit (13344 is not 13345); fuzzy for words (PLAN P3)."""
    a, b = norm(seen), norm(want)
    if a == b or re.search(r"\d", b):
        return a == b
    return difflib.SequenceMatcher(None, a, b).ratio() >= cfg.fuzzy


def typed_ok(seen: str, want: str, cfg: ReplayConfig) -> bool:
    """Bug B: the value is one of the OCR words. Digits exact ($10.00 is 10.00); words fuzzy
    (llinois)."""
    words, n = norm(seen).replace("$", "").replace(",", "").split(), len(norm(want).split())
    runs = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    return any(same_text(r, want.replace("$", "").replace(",", ""), cfg) for r in runs)


def same_label(seen: str, label: str, cfg: ReplayConfig) -> bool:
    """Rung 2 anchors only. Discovery saves labels cleaned ('to account #'); live OCR may merge
    the label with its field's value ('to account #[16785'). Strip `[ ] |`, then a label at the
    start counts. Else fuzzy, but the first word must match too: 'From account #' is 0.85 like
    'to account #'."""
    a, b = norm(re.sub(r"[\[\]|]", " ", seen)), norm(re.sub(r"[\[\]|]", " ", label))
    if b and a.startswith(b):
        return True

    def first(t: str) -> str:
        return (t.split() or [""])[0]  # 'From account #' is not 'to account #'

    return same_text(a, b, cfg) and same_text(first(a), first(b), cfg)


def find_text(
    look: Look,
    text: str,
    ordinal: int,
    cfg: ReplayConfig,
    match: SameTextLike = same_text,
) -> Element | None:
    hits = [e for e in look.elements if match(e.text, text, cfg)]
    return hits[ordinal - 1] if len(hits) >= ordinal else None


def find_template(
    img: NDArray[np.uint8], tpl: NDArray[np.uint8], cfg: ReplayConfig
) -> tuple[int, int] | None:
    """Centre of the one clear best match; two near-equal peaks count as a miss."""
    h, w = tpl.shape[:2]
    if h > img.shape[0] or w > img.shape[1]:
        return None
    res = np.nan_to_num(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED), nan=-1.0)
    _, best, _, (x, y) = cv2.minMaxLoc(res)
    res[max(y - h // 2, 0) : y + h // 2 + 1, max(x - w // 2, 0) : x + w // 2 + 1] = -1
    if best < cfg.template_threshold or cv2.minMaxLoc(res)[1] > best - cfg.template_margin:
        return None
    return x + w // 2, y + h // 2


def read_cell(
    look: Look, cell: TableCell, values: dict[str, str], cfg: ReplayConfig
) -> Element | None:
    """Q8: the element on the row-key's row, under the column header."""
    key = find_text(look, fill(cell.row_key, values), 1, cfg)
    head = find_text(look, cell.column, 1, cfg)
    if not key or not head:
        return None
    return next(
        (
            e
            for e in look.elements
            if e is not key
            and e.box.y1 < key.box.y2
            and key.box.y1 < e.box.y2
            and head.box.x1 < e.box.x2
            and e.box.x1 < head.box.x2
        ),
        None,
    )


def anchor_point(
    look: Look, a: Anchor | None, values: dict[str, str], cfg: ReplayConfig
) -> tuple[int, int] | None:
    """Rung 2's point: the anchor label's centre plus the recorded offset."""
    if a is None:
        return None
    el = find_text(look, fill(a.label, values), a.ordinal, cfg, same_label)
    return (el.box.center[0] + a.offset[0], el.box.center[1] + a.offset[1]) if el else None


def text_hit(
    look: Look,
    text: str,
    ordinal: int,
    near: tuple[int, int] | None,
    cfg: ReplayConfig,
) -> tuple[tuple[int, int], str] | None:
    """Rung 1. The same text twice (a menu link and a page heading): the copy nearest the
    anchor's point wins; none near it = no hit, so rung 2 (the anchor itself) decides."""
    hits = [e for e in look.elements if same_text(e.text, text, cfg)]
    if len(hits) < 2 or near is None:  # noqa: PLR2004
        el = hits[ordinal - 1] if len(hits) >= ordinal else None
        return (el.box.center, "rung1") if el else None
    best = min(hits, key=lambda e: math.dist(e.box.center, near))
    if math.dist(best.box.center, near) > cfg.near_px:
        return None
    by_ordinal = hits[ordinal - 1] if len(hits) >= ordinal else None
    return best.box.center, "rung1" if best is by_ordinal else "rung1+anchor"


def _ocr_hit(
    look: Look,
    text: OcrText | None,
    values: dict[str, str],
    near: tuple[int, int] | None,
    cfg: ReplayConfig,
) -> tuple[tuple[int, int], str] | None:
    """Rung 1: the target's own OCR text, if it has one."""
    return text_hit(look, fill(text.text, values), text.ordinal, near, cfg) if text else None


def locate(
    look: Look,
    target: Target,
    values: dict[str, str],
    crops: Path | None,
    cfg: ReplayConfig,
) -> tuple[tuple[int, int], str] | None:
    """(point, rung) from the first rung that hits, or None."""
    if (c := target.table_cell) and (el := read_cell(look, c, values, cfg)):
        return el.box.center, "table"
    near = anchor_point(look, target.anchor, values, cfg)
    if hit := _ocr_hit(look, target.ocr_text, values, near, cfg):
        return hit
    if near:
        return near, "rung2"
    if target.template and crops is not None:
        tpl = cv2.imread(str(crops / target.template))
        if (p := find_template(decode(look.png), tpl, cfg)) is not None:  # type: ignore[arg-type]
            return p, "rung3"
    return None

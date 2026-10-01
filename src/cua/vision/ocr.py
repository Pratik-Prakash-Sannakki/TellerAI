"""The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.

Moved from the discovery notebook: ``OCR_ENGINE = RapidOCR()`` at import (discovery.py 187)
becomes a lazily-built, ``functools.cache``d :func:`ocr_engine` -- importing ``cua.vision`` must
never load the model. ``ocr`` (200-209; ``CFG.ocr_min_score`` becomes the ``min_score`` parameter),
``number`` (212-225; the module-level ``REFS = {"next": 1}`` becomes :class:`RefCounter`, owned by
the run and passed in), ``draw_numbered`` (228-235).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import cv2
import numpy as np
from numpy.typing import NDArray

from cua.vision.look import Box, Element

if TYPE_CHECKING:
    from rapidocr import RapidOCR


@functools.cache
def ocr_engine() -> RapidOCR:
    """The RapidOCR engine, built once per process. rapidocr is imported here only, so importing
    ``cua.vision`` (or anything it re-exports) never loads the model."""
    from rapidocr import RapidOCR

    return RapidOCR()


@dataclass
class RefCounter:
    """Fresh element refs for one run. Refs grow for the whole run and are never reused, so a
    reference the model saw once always means the same element (the old module-level
    ``REFS = {"next": 1}``, now owned by the caller instead of the module)."""

    _next: int = field(default=1)

    def take(self) -> int:
        ref = self._next
        self._next += 1
        return ref


def ocr(img: NDArray[np.uint8], min_score: float) -> list[tuple[str, Box]]:
    out = ocr_engine()(img)
    if out.boxes is None:
        return []
    items = []
    for quad, txt, score in zip(out.boxes, out.txts, out.scores):
        if score >= min_score and txt.strip():
            xs, ys = [p[0] for p in quad], [p[1] for p in quad]
            items.append((txt.strip(), Box(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))))
    return items


def number(items: list[tuple[str, Box]], refs: RefCounter) -> tuple[Element, ...]:
    """Reading order (rows top to bottom, then left to right), fresh refs."""
    rows: list[list[tuple[str, Box]]] = []
    for it in sorted(items, key=lambda t: t[1].y1):
        first = rows[-1][0][1] if rows else None
        if first and it[1].y1 < first.y2 and it[1].y2 > first.y1:
            rows[-1].append(it)
        else:
            rows.append([it])
    out = []
    for text, box in (it for row in rows for it in sorted(row, key=lambda t: t[1].x1)):
        out.append(Element(refs.take(), text, box))
    return tuple(out)


def draw_numbered(img: NDArray[np.uint8], elements: tuple[Element, ...]) -> bytes:
    out = img.copy()
    for e in elements:
        b = e.box
        cv2.rectangle(out, (b.x1, b.y1), (b.x2, b.y2), (0, 0, 255), 1)
        cv2.putText(
            out,
            str(e.ref),
            (b.x1, max(b.y1 - 3, 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 0, 255),
            1,
        )
    return cv2.imencode(".png", out)[1].tobytes()

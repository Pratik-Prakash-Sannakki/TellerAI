"""Box, Element, Look: the shapes every vision/discovery/replay function reads and writes.

Moved verbatim from the discovery notebook (``Box``/``Element``/``Look`` at discovery.py 146-184,
``decode``/``encode`` at 192-197). No I/O; imports nothing else from ``cua``.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def overlaps(self, o: Box) -> bool:
        return self.x1 < o.x2 and o.x1 < self.x2 and self.y1 < o.y2 and o.y1 < self.y2


@dataclass(frozen=True)
class Element:
    ref: int
    text: str
    box: Box


@dataclass(frozen=True)
class Look:
    png: bytes  # screenshot at the model's canvas size (crops come from this)
    drawn: bytes  # with numbered boxes (what the model sees)
    elements: tuple[Element, ...]
    url: str
    scale: float = 1.0  # canvas pixels -> page points (mouse)

    def get(self, ref: int) -> Element | None:
        return next((e for e in self.elements if e.ref == ref), None)

    @property
    def text(self) -> str:
        return " ".join(e.text for e in self.elements)


def decode(png: bytes) -> NDArray[np.uint8]:
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)


def encode(img: NDArray[np.uint8]) -> bytes:
    return cv2.imencode(".png", img)[1].tobytes()

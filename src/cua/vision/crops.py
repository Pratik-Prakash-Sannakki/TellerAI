"""Crops around one point: find the element there, crop around it, read text near it, and tell
whether two looks differ at that point.

Moved verbatim (bodies unchanged) from the discovery notebook: ``element_at`` (discovery.py
327-328), ``crop_box`` (374-382), ``cut_crop`` (385-393), ``read_near`` (396-398), ``spot_changed``
(401-405), ``screens_same`` (408-410). ``crop_box`` called ``canvas()`` (the size of the CURRENT
look); here the caller passes that size explicitly, and ``cut_crop``/``read_near``/``spot_changed``
take the same ``size`` plus the ``BrowserConfig`` subset they need (``crop_pad``/``point_crop``/
``same_screen_mad``).
"""

from __future__ import annotations

import cv2
import numpy as np

from cua.config import BrowserConfig
from cua.vision.look import Box, Element, Look, decode


def element_at(look: Look, point: tuple[int, int]) -> Element | None:
    return next((e for e in look.elements if e.box.contains(*point)), None)


def crop_box(
    point: tuple[int, int], el: Element | None, size: tuple[int, int], cfg: BrowserConfig
) -> Box:
    w, h = size
    if el:
        p = cfg.crop_pad
        b = Box(el.box.x1 - p, el.box.y1 - p, el.box.x2 + p, el.box.y2 + p)
    else:
        cw, ch = cfg.point_crop
        b = Box(point[0] - cw // 2, point[1] - ch // 2, point[0] + cw // 2, point[1] + ch // 2)
    return Box(max(b.x1, 0), max(b.y1, 0), min(b.x2, w), min(b.y2, h))


def cut_crop(
    look: Look,
    point: tuple[int, int],
    keep: Element | None,
    size: tuple[int, int],
    cfg: BrowserConfig,
) -> bytes:
    """Crop around the target, with every other piece of text blanked out."""
    b = crop_box(point, keep, size, cfg)
    crop = decode(look.png)[b.y1 : b.y2, b.x1 : b.x2].copy()
    fill = np.median(crop.reshape(-1, 3), axis=0)
    for e in look.elements:
        if e is not keep and e.box.overlaps(b):
            crop[
                max(e.box.y1 - b.y1, 0) : e.box.y2 - b.y1, max(e.box.x1 - b.x1, 0) : e.box.x2 - b.x1
            ] = fill
    return cv2.imencode(".png", crop)[1].tobytes()


def read_near(look: Look, point: tuple[int, int], size: tuple[int, int], cfg: BrowserConfig) -> str:
    b = crop_box(point, None, size, cfg)
    return " ".join(e.text for e in look.elements if e.box.overlaps(b))


def spot_changed(
    before: Look,
    after: Look,
    point: tuple[int, int],
    size: tuple[int, int],
    cfg: BrowserConfig,
) -> bool:
    """Pixels around the point changed. Catches password dots that OCR cannot read."""
    b = crop_box(point, None, size, cfg)
    a, z = (decode(x.png)[b.y1 : b.y2, b.x1 : b.x2] for x in (before, after))
    return float(np.mean(cv2.absdiff(a, z))) >= cfg.same_screen_mad


def screens_same(a: bytes, b: bytes, cfg: BrowserConfig) -> bool:
    ga, gb = (cv2.cvtColor(decode(p), cv2.COLOR_BGR2GRAY) for p in (a, b))
    return float(np.mean(cv2.absdiff(ga, gb))) < cfg.same_screen_mad

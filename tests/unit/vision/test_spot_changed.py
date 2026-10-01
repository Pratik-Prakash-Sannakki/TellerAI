"""spot_changed: password dots are pixels, not OCR text.

Ported from tests/discovery/test_spot_changed.py against cua.vision.crops (CFG.point_crop /
CFG.same_screen_mad -> explicit cfg; canvas() size -> an explicit `size` parameter, per the
step-2 brief).
"""

from __future__ import annotations

import cv2
import numpy as np

from cua.config import BrowserConfig
from cua.vision.crops import spot_changed
from cua.vision.look import Look

CFG = BrowserConfig(viewport=(200, 100), point_crop=(60, 30), same_screen_mad=1.0)


def _look(img: np.ndarray) -> Look:
    png = cv2.imencode(".png", img)[1].tobytes()
    return Look(png, png, (), "u")


def test_dots_count_as_change_and_blank_does_not() -> None:
    blank = np.full((100, 200, 3), 255, np.uint8)
    dotted = blank.copy()
    for x in range(80, 120, 8):
        cv2.circle(dotted, (x, 50), 3, (0, 0, 0), -1)
    size = (200, 100)
    assert spot_changed(_look(blank), _look(dotted), (100, 50), size, CFG)
    assert not spot_changed(_look(blank), _look(blank.copy()), (100, 50), size, CFG)

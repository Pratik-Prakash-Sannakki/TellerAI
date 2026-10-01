"""crop_box/cut_crop/read_near/element_at/screens_same: the crop and comparison helpers replay
and discovery both use to look closely at one point."""

from __future__ import annotations

import cv2
import numpy as np

from cua.config import BrowserConfig
from cua.vision.crops import crop_box, cut_crop, element_at, read_near, screens_same
from cua.vision.look import Box, Element, Look

CFG = BrowserConfig(viewport=(200, 100), crop_pad=6, point_crop=(60, 30), same_screen_mad=1.0)


def _look(img: np.ndarray, elements: tuple[Element, ...] = ()) -> Look:
    png = cv2.imencode(".png", img)[1].tobytes()
    return Look(png, png, elements, "u")


def test_element_at_finds_the_element_containing_the_point() -> None:
    el = Element(1, "Log In", Box(0, 0, 10, 10))
    look = Look(b"", b"", (el,), "u")
    assert element_at(look, (5, 5)) is el
    assert element_at(look, (50, 50)) is None


def test_crop_box_around_an_element_adds_the_pad_and_clips_to_the_canvas() -> None:
    el = Element(1, "x", Box(0, 0, 10, 10))
    b = crop_box((5, 5), el, (200, 100), CFG)
    assert b == Box(0, 0, 16, 16)  # x1/y1 clipped at 0; x2/y2 padded by crop_pad


def test_crop_box_around_a_bare_point_uses_point_crop() -> None:
    b = crop_box((100, 50), None, (200, 100), CFG)
    cw, ch = CFG.point_crop
    assert b == Box(100 - cw // 2, 50 - ch // 2, 100 + cw // 2, 50 + ch // 2)


def test_cut_crop_blanks_out_every_other_elements_text() -> None:
    img = np.zeros((100, 200, 3), np.uint8)
    img[40:60, 40:60] = (10, 20, 30)  # the kept element
    img[40:60, 70:90] = (200, 200, 200)  # another element, inside the crop, must be blanked
    keep = Element(1, "keep", Box(40, 40, 60, 60))
    other = Element(2, "other", Box(70, 40, 90, 60))
    look = _look(img, (keep, other))
    cfg = BrowserConfig(viewport=(200, 100), crop_pad=50, point_crop=(60, 30), same_screen_mad=1.0)
    out = cv2.imdecode(
        np.frombuffer(cut_crop(look, (50, 50), keep, (200, 100), cfg), np.uint8), cv2.IMREAD_COLOR
    )
    # crop_box: Box(40-50, 40-50, 60+50, 60+50) clipped to (0,0,200,100) -> (0,0,110,100)
    assert tuple(out[50, 50]) == (10, 20, 30)  # kept pixel untouched (crop origin (0,0))
    assert tuple(int(c) for c in out[50, 80]) != (200, 200, 200)  # other element's pixel blanked


def test_read_near_joins_every_elements_text_overlapping_the_crop() -> None:
    img = np.zeros((100, 200, 3), np.uint8)
    near = Element(1, "near", Box(90, 40, 110, 60))
    far = Element(2, "far", Box(0, 0, 5, 5))
    look = _look(img, (near, far))
    assert read_near(look, (100, 50), (200, 100), CFG) == "near"


def test_screens_same_is_true_for_identical_images_and_false_for_different_ones() -> None:
    blank = np.full((100, 200, 3), 255, np.uint8)
    dotted = blank.copy()
    cv2.circle(dotted, (100, 50), 10, (0, 0, 0), -1)
    a, b = cv2.imencode(".png", blank)[1].tobytes(), cv2.imencode(".png", blank.copy())[1].tobytes()
    assert screens_same(a, b, CFG)
    assert not screens_same(a, cv2.imencode(".png", dotted)[1].tobytes(), CFG)

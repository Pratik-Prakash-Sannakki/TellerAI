"""take_look's canvas: any window size or pixel density maps to one grid, and clicks map back.

Ported from tests/discovery/test_canvas.py against cua.vision.canvas (the old ast-exec file is
deleted in this step: HANDOFF.look -> an explicit `look` parameter, per the step-2 brief).
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from cua.vision.canvas import canvas_size, to_canvas, to_page
from cua.vision.look import Look

CANVAS_VIEWPORT = (1280, 800)


@pytest.mark.parametrize(
    ("shot", "points_w"),
    [
        ((1600, 2880), 1440),  # Retina 2x, 1440x800 window: the case that broke login
        ((800, 1280), 1280),  # the old fixed page, 1x
        ((1050, 1680), 1680),  # big 1x window
        ((900, 1200), 1200),  # narrow window
    ],
)
def test_fits_canvas_and_maps_clicks_back_to_the_same_spot(
    shot: tuple[int, int], points_w: int
) -> None:
    img = np.zeros((*shot, 3), np.uint8)
    out, scale = to_canvas(img, points_w, CANVAS_VIEWPORT)
    assert out.shape[1] <= CANVAS_VIEWPORT[0]  # never wider than the canvas
    assert out.shape[0] <= CANVAS_VIEWPORT[1]  # never taller than the canvas
    right_edge = to_page(None, (out.shape[1], 0))[0]
    assert right_edge == out.shape[1]  # no look yet: scale 1.0, so page == canvas pixels
    look = Look(b"", b"", (), "u", scale=scale)
    right_edge = to_page(look, (out.shape[1], 0))[0]
    assert right_edge == pytest.approx(points_w, abs=1)  # canvas edge = window edge


def test_canvas_size_is_the_viewport_when_there_is_no_look_yet() -> None:
    assert canvas_size(None, CANVAS_VIEWPORT) == CANVAS_VIEWPORT


def test_canvas_size_is_the_current_looks_own_png_size() -> None:
    img = np.zeros((100, 200, 3), np.uint8)
    png = cv2.imencode(".png", img)[1].tobytes()
    look = Look(png, png, (), "u")
    assert canvas_size(look, CANVAS_VIEWPORT) == (200, 100)

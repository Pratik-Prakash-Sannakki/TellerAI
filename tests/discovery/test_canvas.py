"""take_look's canvas: any window size or pixel density maps to one grid, and clicks map back."""
import ast
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


def _ns(look=None):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"to_canvas", "to_page"}]
    ns = {"cv2": cv2, "np": np, "CFG": SimpleNamespace(viewport=(1280, 800)),
          "HANDOFF": SimpleNamespace(look=look)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


@pytest.mark.parametrize(("shot", "points_w"), [
    ((1600, 2880), 1440),   # Retina 2x, 1440x800 window: the case that broke login
    ((800, 1280), 1280),    # the old fixed page, 1x
    ((1050, 1680), 1680),   # big 1x window
    ((900, 1200), 1200),    # narrow window
])
def test_fits_canvas_and_maps_clicks_back_to_the_same_spot(shot, points_w) -> None:
    ns = _ns()
    img = np.zeros((*shot, 3), np.uint8)
    out, scale = ns["to_canvas"](img, points_w)
    assert out.shape[1] <= 1280 and out.shape[0] <= 800            # never larger than the canvas
    ns["HANDOFF"].look = SimpleNamespace(scale=scale)
    right_edge = ns["to_page"]((out.shape[1], 0))[0]
    assert right_edge == pytest.approx(points_w, abs=1)             # canvas edge = window edge

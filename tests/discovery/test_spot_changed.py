"""spot_changed: password dots are pixels, not OCR text."""
import ast
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
NAMES = {"Box", "crop_box", "spot_changed", "decode"}


def _load() -> dict:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in NAMES]
    ns = {"np": np, "cv2": cv2, "dataclass": __import__("dataclasses").dataclass,
          "Element": object, "Look": object, "canvas": lambda: (200, 100),
          "CFG": SimpleNamespace(viewport=(200, 100), point_crop=(60, 30), same_screen_mad=1.0)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def _look(img: np.ndarray) -> SimpleNamespace:
    return SimpleNamespace(png=cv2.imencode(".png", img)[1].tobytes())


def test_dots_count_as_change_and_blank_does_not() -> None:
    ns = _load()
    blank = np.full((100, 200, 3), 255, np.uint8)
    dotted = blank.copy()
    for x in range(80, 120, 8):
        cv2.circle(dotted, (x, 50), 3, (0, 0, 0), -1)
    assert ns["spot_changed"](_look(blank), _look(dotted), (100, 50))
    assert not ns["spot_changed"](_look(blank), _look(blank.copy()), (100, 50))

"""number()'s reading order and ref continuity; ocr_engine() built lazily, never on import."""

from __future__ import annotations

import subprocess
import sys

from cua.vision.look import Box
from cua.vision.ocr import RefCounter, number


def test_ref_counter_starts_at_one_and_never_reuses_a_ref() -> None:
    refs = RefCounter()
    assert [refs.take(), refs.take(), refs.take()] == [1, 2, 3]


def test_number_orders_rows_top_to_bottom_then_left_to_right() -> None:
    items = [
        ("b", Box(100, 0, 150, 20)),
        ("a", Box(0, 0, 50, 20)),
        ("c", Box(0, 30, 50, 50)),
    ]
    out = number(items, RefCounter())
    assert [e.text for e in out] == ["a", "b", "c"]
    assert [e.ref for e in out] == [1, 2, 3]


def test_number_groups_items_whose_rows_overlap_vertically() -> None:
    items = [("x", Box(0, 0, 10, 20)), ("y", Box(5, 10, 15, 30))]
    out = number(items, RefCounter())
    assert [e.text for e in out] == ["x", "y"]  # same row (y1<first.y2 and y2>first.y1): x first


def test_refs_are_never_reused_across_separate_number_calls() -> None:
    """The RefCounter is owned by the run, not by number(), so refs keep growing call to call."""
    refs = RefCounter()
    first = number([("a", Box(0, 0, 10, 10))], refs)
    second = number([("b", Box(0, 0, 10, 10))], refs)
    assert [first[0].ref, second[0].ref] == [1, 2]


def test_importing_cua_vision_does_not_import_rapidocr() -> None:
    """ocr_engine() must build the model lazily: importing the package alone must not load it."""
    out = subprocess.run(
        [sys.executable, "-c", "import cua.vision; import sys; print('rapidocr' in sys.modules)"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "False"

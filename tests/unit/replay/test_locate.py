"""cua.replay.locate: the 3 rungs + table cell; all miss -> None.

Ported from tests/replay/test_rungs.py (all tests) and the one locate-relevant test in
tests/replay/test_checks.py (typed_ok). CFG.fuzzy/template_threshold/template_margin/near_px are
now a `cfg: ReplayConfig` parameter threaded through, instead of a module global.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from cua.config import ReplayConfig
from cua.replay import find_text, locate, same_label, typed_ok
from cua.schema import Anchor, OcrText, TableCell, Target
from cua.vision import Box, Element, Look, encode

CFG = ReplayConfig()

ACCOUNTS = [
    ("Account", (10, 10, 80, 30)),
    ("Balance", (200, 10, 270, 30)),
    ("13344", (10, 50, 60, 70)),
    ("$515.50", (200, 50, 260, 70)),
    ("13345", (10, 90, 60, 110)),
    ("$100.00", (200, 90, 260, 110)),
]


def _look(items: list[tuple[str, tuple[int, int, int, int]]], png: bytes = b"") -> Look:
    els = tuple(Element(i, t, Box(*b)) for i, (t, b) in enumerate(items, 1))
    return Look(png, png, els, "https://parabank.parasoft.com/parabank/x.htm")


def test_rung1_text_and_ordinal() -> None:
    lk = _look([("Amount", (0, 0, 40, 10)), ("Amount", (0, 100, 40, 110))])
    t = Target(
        ocr_text=OcrText(text="Amount", ordinal=2),
        anchor=Anchor(label="Amount", ordinal=2, offset=(0, 0)),
    )
    assert locate(lk, t, {}, None, CFG) == ((20, 105), "rung1")


def test_rung1_digits_exact_words_fuzzy() -> None:
    lk = _look([("13345", (0, 0, 40, 10)), ("Log ln", (0, 50, 40, 60))])
    assert find_text(lk, "13344", 1, CFG) is None
    found = find_text(lk, "Log In", 1, CFG)
    assert found is not None
    assert found.text == "Log ln"


def test_rung2_anchor_offset() -> None:
    lk = _look([("Password", (40, 200, 80, 220))])
    t = Target(anchor=Anchor(label="Password", offset=(150, 0)))
    assert locate(lk, t, {}, None, CFG) == ((210, 210), "rung2")


def test_rung3_template(tmp_path: Path) -> None:
    img = np.full((200, 300, 3), 255, np.uint8)
    cv2.rectangle(img, (120, 80), (180, 110), (0, 0, 0), 2)
    cv2.putText(img, "Go", (135, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)
    cv2.imwrite(str(tmp_path / "c.png"), img[74:117, 114:187])
    t = Target(template="c.png")
    hit = locate(_look([], encode(img)), t, {}, tmp_path, CFG)
    assert hit is not None
    (x, y), rung = hit
    tolerance = 2
    assert rung == "rung3"
    assert abs(x - 150) <= tolerance
    assert abs(y - 95) <= tolerance


def test_table_cell_by_row_key_input() -> None:
    t = Target(table_cell=TableCell(row_key="{{account_id}}", column="Balance"))
    hit = locate(_look(ACCOUNTS), t, {"account_id": "13345"}, None, CFG)
    assert hit == ((230, 100), "table")


def test_all_miss_is_none(tmp_path: Path) -> None:
    img = np.full((200, 300, 3), 255, np.uint8)
    tpl = np.zeros((20, 20, 3), np.uint8)
    cv2.circle(tpl, (10, 10), 6, (255, 255, 255), -1)
    cv2.imwrite(str(tmp_path / "c.png"), tpl)
    t = Target(
        ocr_text=OcrText(text="Transfer"),
        anchor=Anchor(label="Amount", offset=(5, 0)),
        template="c.png",
    )
    lk = _look([("Home", (0, 0, 30, 10))], encode(img))
    assert locate(lk, t, {}, tmp_path, CFG) is None


def test_anchor_label_matches_ocr_merged_with_a_value() -> None:
    for seen in (
        "to account #16785",
        "to account #123456789",
        "To account #[16785]",
        "to account #",
    ):
        assert same_label(seen, "to account #", CFG), seen
    assert same_label("From account #[", "From account #", CFG)
    assert same_label("| From account #", "From account #", CFG)
    assert not same_label("to amount", "to account #", CFG)
    assert not same_label("to account #16785", "to amount", CFG)


def test_rung2_hits_a_merged_label_but_rung1_stays_exact() -> None:
    lk = _look([("to account #123456789", (40, 200, 200, 220))])
    anchor = Target(anchor=Anchor(label="to account #", offset=(150, 0)))
    assert locate(lk, anchor, {}, None, CFG) == ((270, 210), "rung2")
    value = Target(
        ocr_text=OcrText(text="to account #1"),
        anchor=Anchor(label="nothing here", offset=(0, 0)),
    )
    assert locate(lk, value, {}, None, CFG) is None  # a value to click is never a prefix match


MENU = [
    ("Open New Account", (300, 250, 420, 266)),
    ("Accounts Overview", (300, 274, 420, 290)),
    ("Accounts Overview", (500, 280, 640, 296)),
]  # the menu link, then the page heading


def _dup_target(offset: tuple[int, int]) -> Target:
    return Target(
        ocr_text=OcrText(text="Accounts Overview", ordinal=1),
        anchor=Anchor(label="Open New Account", offset=offset),
    )


def test_duplicate_text_picks_the_copy_nearest_the_anchor() -> None:
    lk = _look(list(reversed(MENU)))  # the heading comes first in reading order
    assert locate(lk, _dup_target((-1, 24)), {}, None, CFG) == ((360, 282), "rung1+anchor")
    lk = _look(MENU)
    assert locate(lk, _dup_target((210, 30)), {}, None, CFG) == ((570, 288), "rung1+anchor")


def test_duplicate_text_with_no_copy_near_the_anchor_uses_rung2() -> None:
    lk = _look(MENU)
    assert locate(lk, _dup_target((0, 200)), {}, None, CFG) == ((360, 458), "rung2")


def test_a_single_text_match_is_rung1_as_before() -> None:
    lk = _look(MENU[:2])
    assert locate(lk, _dup_target((0, 200)), {}, None, CFG) == ((360, 282), "rung1")


def test_typed_ok_words_tolerant_digits_exact() -> None:
    assert typed_ok("llinois", "Illinois", CFG)
    assert typed_ok("IL", "IL", CFG)
    assert typed_ok("10", "10", CFG)
    assert typed_ok("$10.00", "10.00", CFG)
    assert not typed_ok("13345", "13344", CFG)
    assert not typed_ok("100", "10", CFG)
    assert not typed_ok("", "IL", CFG)

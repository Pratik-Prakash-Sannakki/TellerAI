"""Step checks on fakes: whole-field read (A), tolerant word match (B), late page change (D)."""
import asyncio

import cv2
import numpy as np

FIELD = (300, 100, 500, 130)     # a drawn input box; its centre is (400, 115)


def _form_png(ns) -> bytes:
    img = np.full((300, 700, 3), 255, np.uint8)
    cv2.rectangle(img, FIELD[:2], FIELD[2:], (160, 160, 160), 1)
    return ns["encode"](img)


def test_field_box_is_the_drawn_input(ns, mk_look) -> None:
    lk = mk_look([], _form_png(ns))
    ns["STATE"].look = lk
    b = ns["field_box"](lk, (400, 115))
    assert abs(b.x1 - 300) <= 2 and abs(b.x2 - 500) <= 2 and abs(b.y1 - 100) <= 2 and abs(b.y2 - 130) <= 2


def test_short_value_at_left_edge_is_read(ns, mk_look) -> None:
    lk = mk_look([("State", (220, 108, 270, 124)), ("IL", (306, 108, 322, 124))], _form_png(ns))
    ns["STATE"].look = lk
    assert ns["read_field"](lk, (400, 115)) == "IL"


def test_typed_ok_words_tolerant_digits_exact(ns) -> None:
    ok = ns["typed_ok"]
    assert ok("llinois", "Illinois")
    assert ok("IL", "IL") and ok("10", "10") and ok("$10.00", "10.00")
    assert not ok("13345", "13344") and not ok("100", "10")
    assert not ok("", "IL")


class _Page:
    url = "https://parabank.parasoft.com/parabank/billpay.htm"

    async def wait_for_timeout(self, ms) -> None:
        return None

    async def evaluate(self, js, *args) -> list:
        return []


def test_click_waits_for_a_late_page_change(ns, mk_look) -> None:
    blank = mk_look([("Pay", (10, 10, 40, 30))], ns["encode"](np.full((80, 80, 3), 255, np.uint8)))
    done = mk_look([("Complete", (10, 10, 70, 30))], ns["encode"](np.zeros((80, 80, 3), np.uint8)))
    looks = iter([blank, done, done])

    async def act(*steps):
        ns["STATE"].look = blank
        return blank

    async def take_look():
        ns["STATE"].look = next(looks, done)
        return ns["STATE"].look

    ns.update(act=act, take_look=take_look, page=_Page())
    ns["STATE"].look = blank
    step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": "Pay"}, "anchor": {"label": "Pay", "offset": [0, 0]}})
    assert asyncio.run(ns["do_click"](step, (25, 20), None)) is True
    assert ns["STATE"].look is done

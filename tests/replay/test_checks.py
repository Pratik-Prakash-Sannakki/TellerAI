"""Step checks on fakes: whole-field read (A), tolerant word match (B), late page change (D)."""
import asyncio
import contextlib

import cv2
import numpy as np
import pytest

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
        await asyncio.sleep(ms / 1000)        # like Playwright: the loop runs meanwhile

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


class _Lock:
    @contextlib.asynccontextmanager
    async def open(self):
        yield


def _white(ns, lines=()):
    img = np.full((400, 600, 3), 255, np.uint8)
    for y in lines:                                     # a few short text-like strokes: a small change
        img[y:y + 6, 20:120] = 0
    return ns["encode"](img)


def _click_env(ns, mk_look, gate_starts_after_s):
    """The real `act`. The click's send takes the gate only after the settle, as a slow route can."""
    form = mk_look([("TRANSFER", (10, 10, 70, 30))], _white(ns))
    done = mk_look([("Transfer Complete!", (10, 10, 170, 30))], _white(ns, [60]))
    page = _Page()
    screen = {"now": form}
    ns["CFG"] = ns["Config"](check_s=0.05, poll_ms=10, settle_ms=10)

    async def gates_then_answer():
        await asyncio.sleep(gate_starts_after_s)
        async with ns["SEND_GATE"]:                    # the human takes longer than check_s
            ns["STATE"].sent = True
            await asyncio.sleep(0.2)
            ns["STATE"].verdict = "SENT: a human approved both gates."
        screen["now"] = done                           # the site answers once the send is released

    class Mouse:
        async def click(self, *a):
            asyncio.get_running_loop().create_task(gates_then_answer())

    async def take_look():
        ns["STATE"].look = screen["now"]
        return screen["now"]

    page.mouse = Mouse()
    ns.update(take_look=take_look, page=page, LOCK=_Lock())
    ns["STATE"].look = form
    step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": "TRANSFER"},
                                         "anchor": {"label": "TRANSFER", "offset": [0, 0]}})
    return step, done


@pytest.mark.parametrize("gate_starts_after_s", [0, 0.03])
def test_a_send_approved_after_check_s_still_passes_with_no_rescue(ns, mk_look, gate_starts_after_s) -> None:
    """Live bug: the Transfer click sent (both gates approved) but its check said 'failed'."""
    step, done = _click_env(ns, mk_look, gate_starts_after_s)
    assert asyncio.run(asyncio.wait_for(ns["do_click"](step, (40, 20), None), 2)) is True
    assert ns["STATE"].look is done


def test_a_small_change_with_new_text_counts_as_a_change(ns, mk_look) -> None:
    a = mk_look([("TRANSFER", (10, 10, 70, 30))], _white(ns))
    b = mk_look([("Transfer Complete!", (10, 10, 170, 30))], _white(ns, [60]))
    assert ns["screens_same"](a.png, b.png)             # too small for the pixel check alone
    assert ns["changed"](a, b) and not ns["changed"](a, a)


def test_a_one_character_value_is_checked_by_pixels(ns, mk_look) -> None:
    """Live: Address '1' failed twice: OCR does not read a lone character. The field's pixels changed."""
    blank = _white(ns)
    typed = _white(ns, [60])
    before, after = mk_look([], blank), mk_look([("l", (20, 55, 30, 70))], typed)

    async def act(*steps):
        ns["STATE"].look = after
        return after

    ns.update(act=act)
    ns["STATE"].look, ns["STATE"].values = before, {"address": "1"}
    step = ns["SCHEMA"]["Type"](value="{{address}}", target={"anchor": {"label": "Address:", "offset": [0, 0]}})
    assert asyncio.run(ns["do_type"](step, (70, 62), None)) is True
    ns["STATE"].look, ns["STATE"].values = before, {"address": "12 Main"}
    assert asyncio.run(ns["do_type"](step, (70, 62), None)) is False        # longer values: OCR as before


def _same_screen_click(ns, mk_look, navigated):
    lk = mk_look([("Accounts Overview", (10, 10, 170, 30))], _white(ns))
    page = _Page()

    class Mouse:
        async def click(self, *a):
            if navigated:                                  # a main-frame response for the same path
                ns["STATE"].http = (200, "/parabank/overview.htm")
                ns["STATE"].navs += 1

    async def take_look():
        ns["STATE"].look = lk
        return lk

    page.mouse = Mouse()
    ns.update(take_look=take_look, page=page, LOCK=_Lock(), CFG=ns["Config"](check_s=0.05, poll_ms=10, settle_ms=0))
    ns["STATE"].look = lk
    step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": "Accounts Overview"},
                                         "anchor": {"label": "Accounts Overview", "offset": [0, 0]}})
    return asyncio.run(ns["do_click"](step, (90, 20), None))


def test_a_same_url_reload_counts_as_a_change(ns, mk_look) -> None:
    assert _same_screen_click(ns, mk_look, navigated=True) is True


def test_a_click_on_plain_text_with_no_navigation_still_fails(ns, mk_look) -> None:
    assert _same_screen_click(ns, mk_look, navigated=False) is False

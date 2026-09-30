"""The 3 rungs + table cell; all miss -> None."""
import cv2
import numpy as np

ACCOUNTS = [("Account", (10, 10, 80, 30)), ("Balance", (200, 10, 270, 30)),
            ("13344", (10, 50, 60, 70)), ("$515.50", (200, 50, 260, 70)),
            ("13345", (10, 90, 60, 110)), ("$100.00", (200, 90, 260, 110))]


def test_rung1_text_and_ordinal(ns, mk_look) -> None:
    lk = mk_look([("Amount", (0, 0, 40, 10)), ("Amount", (0, 100, 40, 110))])
    t = ns["Target"](ocr_text={"text": "Amount", "ordinal": 2},
                     anchor={"label": "Amount", "ordinal": 2, "offset": [0, 0]})
    assert ns["locate"](lk, t, {}, None) == ((20, 105), "rung1")


def test_rung1_digits_exact_words_fuzzy(ns, mk_look) -> None:
    lk = mk_look([("13345", (0, 0, 40, 10)), ("Log ln", (0, 50, 40, 60))])
    assert ns["find_text"](lk, "13344") is None
    assert ns["find_text"](lk, "Log In").text == "Log ln"


def test_rung2_anchor_offset(ns, mk_look) -> None:
    lk = mk_look([("Password", (40, 200, 80, 220))])
    t = ns["Target"](anchor={"label": "Password", "offset": [150, 0]})
    assert ns["locate"](lk, t, {}, None) == ((210, 210), "rung2")


def test_rung3_template(ns, mk_look, tmp_path) -> None:
    img = np.full((200, 300, 3), 255, np.uint8)
    cv2.rectangle(img, (120, 80), (180, 110), (0, 0, 0), 2)
    cv2.putText(img, "Go", (135, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)
    cv2.imwrite(str(tmp_path / "c.png"), img[74:117, 114:187])
    ns["STATE"].look = None
    t = ns["Target"](template="c.png")
    (x, y), rung = ns["locate"](mk_look([], ns["encode"](img)), t, {}, tmp_path)
    assert rung == "rung3" and abs(x - 150) <= 2 and abs(y - 95) <= 2


def test_table_cell_by_row_key_input(ns, mk_look) -> None:
    t = ns["Target"](table_cell={"row_key": "{{account_id}}", "column": "Balance"})
    point, rung = ns["locate"](mk_look(ACCOUNTS), t, {"account_id": "13345"}, None)
    assert rung == "table" and point == (230, 100)


def test_all_miss_is_none(ns, mk_look, tmp_path) -> None:
    img = np.full((200, 300, 3), 255, np.uint8)
    tpl = np.zeros((20, 20, 3), np.uint8)
    cv2.circle(tpl, (10, 10), 6, (255, 255, 255), -1)
    cv2.imwrite(str(tmp_path / "c.png"), tpl)
    t = ns["Target"](ocr_text={"text": "Transfer"}, anchor={"label": "Amount", "offset": [5, 0]},
                     template="c.png")
    assert ns["locate"](mk_look([("Home", (0, 0, 30, 10))], ns["encode"](img)), t, {}, tmp_path) is None

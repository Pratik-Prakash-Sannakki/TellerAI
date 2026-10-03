"""Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op clicks dropped.

Ported from tests/discovery/test_wandering.py, test_login_click_kept.py and test_observable.py
(their recorder parts), now against the package. Their tool parts (open_path, value_in_box) are
step 8b's.
"""

from __future__ import annotations

import inspect
import re

import pytest

from cua.discovery.recorder import build_capability, save, step_events
from cua.discovery.tools.read_helpers import spot
from cua.schema import Extract
from cua.vision.look import Box, Look
from cua.vision.ocr import RefCounter, number
from tests.unit.discovery.recorder.test_recorder import LOGIN, SENT, START, _ev, _meta

SITE = "https://parabank.parasoft.com/parabank/"
MENU = ["About Us", "Services", "Products", "Locations", "Admin Page", "Account Services"]
REF = {"ref": 3, "x": None, "y": None}


def _nav(path: str, status: int = 200, before: list[str] = MENU) -> dict:
    ok = status < 400  # noqa: PLR2004
    result = f"Opened {path}." if ok else f"HTTP ERROR {status}: {path} does not exist."
    return {
        **_ev("open_path", {"path": path}, result),
        "url": SITE + path.lstrip("/"),
        "path": "/parabank/" + path.lstrip("/"),
        "status": status,
        "from_texts": before,
    }


def _go(text: str, to: str, before: list[str] = MENU) -> dict:
    return {
        **_ev("click", REF, f"Clicked {text!r}.", own=text, text=text),
        "url": SITE + to,
        "loaded": True,
        "from_texts": before,
    }


EXTRACT = {
    **_ev(
        "extract_value",
        {"ref": 9, "save_as": "bank_phone_number", "value_type": "phone", "description": "phone"},
        "saved",
        label="Customer Care",
    ),
    "url": SITE + "about.htm",
    "pattern": r"\d{3}-\d{3}-\d{4}",
    "table": None,
}


def _paths(steps: list[object]) -> list[str]:
    return [getattr(s, "path", None) or s.target.ocr_text.text for s in steps]  # type: ignore[attr-defined]


def test_a_404_and_detour_navigations_are_dropped() -> None:
    log = [
        START,
        _nav("contact.htm", 404),
        _nav("contact.htm", 404),
        _nav("overview.htm"),
        _nav("index.htm"),
        _go("Contact Us", "contact.htm"),
        _go("About Us", "about.htm"),
        EXTRACT,
    ]
    steps = build_capability(log, _meta(name="phone")).steps
    assert _paths(steps[:-1]) == ["About Us"]  # About Us was on the page all along


def test_consecutive_navigations_keep_only_the_last() -> None:
    log = [START, _nav("overview.htm"), _nav("index.htm"), _nav("about.htm"), EXTRACT]
    assert _paths(build_capability(log, _meta(name="p")).steps[:-1]) == ["/parabank/about.htm"]


def test_a_navigation_needed_to_reach_the_next_link_is_kept() -> None:
    log = [
        START,
        _nav("services.htm"),
        _go("Bookstore", "books.htm", before=["Services", "Bookstore"]),
        EXTRACT,
    ]
    log[1]["from_texts"] = MENU  # 'Bookstore' is only on services.htm
    got = _paths(build_capability(log, _meta(name="p")).steps[:-1])
    assert got == ["/parabank/services.htm", "Bookstore"]


def test_a_click_that_stays_on_the_page_is_never_a_detour() -> None:
    fill = _ev("click", REF, "Clicked 'Services'.", own="Services", text="Services")
    log = [START, fill, _go("About Us", "about.htm"), EXTRACT]
    assert _paths(build_capability(log, _meta(name="p")).steps[:-1]) == ["Services", "About Us"]


def test_a_navigate_step_is_saved_absolute_from_the_origin() -> None:
    log = [START, _nav("about.htm"), EXTRACT]
    assert build_capability(log, _meta(name="p")).steps[0].path == "/parabank/about.htm"  # type: ignore[union-attr]


def test_the_pattern_is_saved_on_the_extract_step_never_the_value() -> None:
    cap = build_capability([START, EXTRACT], _meta(name="p"))
    assert cap.steps[0].pattern == "\\d{3}-\\d{3}-\\d{4}"
    assert cap.outputs[0].type == "phone"  # type: ignore[union-attr]
    assert Extract(target=cap.steps[0].target, save_as="x").pattern is None  # type: ignore[union-attr]


def test_text_on_most_looks_is_never_the_checkpoint() -> None:
    start = {
        **START,
        "start_texts": ["Customer Login"],
        "looks": 4,
        "text_counts": {"parasoft demo website": 4, "about us": 3, "customer care": 1},
    }
    read = {**EXTRACT, "page_texts": ["ParaSoft Demo Website", "About Us", "Customer Care"]}
    fin = _ev(
        "finish_business_outcome", {"outcome": "x", "proof_text": "ParaSoft Demo Website"}, "OK"
    )
    assert build_capability([start, read, fin], _meta(name="p")).checkpoint == "Customer Care"


def test_the_read_pages_heading_is_preferred_over_the_values_label() -> None:
    start = {
        **START,
        "start_texts": ["Customer Login"],
        "looks": 3,
        "text_counts": {"parasoft demo website": 3},
    }
    read = {
        **EXTRACT,
        "page_texts": ["ParaSoft Demo Website", "About Us - ParaBank", "Customer Care"],
        "headings": ["ParaSoft Demo Website", "About Us - ParaBank"],
    }
    assert build_capability([start, read], _meta(name="p")).checkpoint == "About Us - ParaBank"


# --- login clicks kept (was test_login_click_kept.py) ---

HOME = ["Customer Login", "Username", "Password", "LOG IN", "Bill Pay", "Transfer Funds"]
MENU2 = ["Accounts Overview", "Transfer Funds", "Bill Pay", "Log Out"]


def _click(
    text: str, frm: str, to: str, before: list[str], label: str | None = None, **kw: object
) -> dict:  # noqa: PLR0913
    return {
        **_ev("click", REF, f"Clicked {text!r}.", label=label, own=text, text=text),
        "url": SITE + to,
        "from_url": SITE + frm,
        "loaded": frm != to,
        "navigated": frm != to,
        "new_texts": True,
        "from_texts": before,
        **kw,
    }


def _type(tool: str, label: str, url: str = "index.htm") -> dict:
    args = {"secret_name": label.casefold()} if tool == "type_secret" else dict(REF)
    return {**_ev(tool, args, "Typed at (300, 200).", label=label), "url": SITE + url}


LOGIN2 = [
    _type("type_secret", "Username"),
    _type("type_secret", "Password"),
    _click("LOG IN", "index.htm", "overview.htm", HOME, label="Password"),
]
BILL_PAY = _click("Bill Pay.", "overview.htm", "billpay.htm", MENU2, label="Transfer Funds")


def _names(steps: list[object]) -> list[str]:
    return [s.target.ocr_text.text if s.action == "click" else s.action for s in steps]  # type: ignore[attr-defined]


def test_the_login_click_before_a_menu_link_is_kept() -> None:
    kept = step_events([START, *LOGIN2, BILL_PAY])
    got = [ev.get("text") or ev["tool"] for ev in kept]
    assert got == ["type_secret", "type_secret", "LOG IN", "Bill Pay."]


def test_a_login_click_that_stays_on_the_page_is_not_a_no_op() -> None:
    same = _click("LOG IN", "index.htm", "index.htm", HOME, label="Password", new_texts=False)
    kept = step_events([START, *LOGIN2[:2], same])
    assert [ev.get("text") for ev in kept][-1] == "LOG IN"


def test_a_pay_bill_log_keeps_login_bill_pay_fields_send_logout() -> None:
    fields = [
        _type("type_text", "Payee Name:", "billpay.htm"),
        _type("type_text", "Amount: $", "billpay.htm"),
    ]
    send = _click("SEND PAYMENT", "billpay.htm", "billpay.htm", MENU2, label="From account #:")
    logout = _click("Log Out", "billpay.htm", "index.htm", MENU2, label="Request Loan")
    cap = build_capability(
        [START, *LOGIN2, BILL_PAY, *fields, send, SENT, logout], _meta(name="pay")
    )
    assert _names(cap.steps) == [
        "type",
        "type",
        "LOG IN",
        "Bill Pay.",
        "type",
        "type",
        "SEND PAYMENT",
        "Log Out",
    ]
    assert cap.steps[-1].cleanup is True  # type: ignore[union-attr]


def test_a_menu_detour_after_login_is_still_dropped() -> None:
    detour = _click("Transfer Funds", "overview.htm", "transfer.htm", MENU2)
    bill = {**BILL_PAY, "from_url": SITE + "transfer.htm"}
    kept = step_events([START, *LOGIN2, detour, bill])
    assert [ev.get("text") for ev in kept][2:] == ["LOG IN", "Bill Pay."]


def test_a_login_click_after_a_scroll_is_still_kept() -> None:
    scroll = {**_ev("scroll", {"direction": "down"}, "Scrolled."), "url": SITE + "index.htm"}
    login = {**LOGIN2[2], "login": True}
    kept = step_events([START, *LOGIN2[:2], scroll, login, BILL_PAY])
    assert [ev.get("text") for ev in kept][-2:] == ["LOG IN", "Bill Pay."]


# --- no-op clicks (was test_observable.py) ---

OVERVIEW = SITE + "overview.htm"


def _noop_click(  # noqa: PLR0913
    text: str,
    result: str | None = None,
    *,
    url: str = OVERVIEW,
    came_from: str = OVERVIEW,
    new: bool = True,
    navigated: bool = True,
) -> dict:
    """navigated: the page loaded (a link, even back to the same URL); new: new text on screen."""
    return {
        **_ev("click", REF, result or f"Clicked {text!r}.", own=text, text=text),
        "url": url,
        "from_url": came_from,
        "loaded": url != came_from,
        "navigated": navigated,
        "new_texts": new,
    }


READ = {
    **_ev(
        "extract_value",
        {"ref": 9, "save_as": "balance", "value_type": "currency", "description": "b"},
        "saved",
        label="Balance*",
    ),
    "url": OVERVIEW,
}


def _clicks(log: list[dict]) -> list[str]:
    steps = build_capability(log, _meta(name="r")).steps
    return [s.target.ocr_text.text for s in steps if s.action == "click"]  # type: ignore[union-attr]


def test_a_run_that_neither_reads_nor_sends_is_refused() -> None:
    log = [
        *LOGIN,
        _noop_click("Accounts Overview"),
        _ev("scroll", {"direction": "down"}, "Scrolled."),
    ]
    with pytest.raises(ValueError, match="nothing was read or sent"):
        build_capability(log, _meta(name="find"))


def test_a_read_or_a_send_is_enough() -> None:
    assert build_capability([*LOGIN, READ], _meta(name="r")).outputs[0].name == "balance"
    assert build_capability([*LOGIN, SENT], _meta(name="s")).steps


def test_the_live_no_op_clicks_are_dropped() -> None:
    """After login the site is already on Accounts Overview; clicking it, scrolling, clicking it."""
    log = [
        *LOGIN,
        _noop_click(
            "Accounts Overview",
            "NO CHANGE after clicking (80, 200). Look again and retry.",
            new=False,
        ),
        _ev("scroll", {"direction": "down"}, "Scrolled."),
        _noop_click("Accounts Overview", new=False),
        READ,
    ]
    steps = build_capability(log, _meta(name="r")).steps
    assert [s.action for s in steps] == ["type", "type", "click", "extract"]


def test_a_click_that_lands_on_the_page_it_left_is_dropped() -> None:
    assert _clicks([*LOGIN, _noop_click("Accounts Overview", new=True), READ]) == ["Log In"]


def test_a_click_that_changes_the_screen_on_the_same_page_is_kept() -> None:
    log = [*LOGIN, _noop_click("Show details", new=True, navigated=False), READ]
    assert _clicks(log) == ["Log In", "Show details"]


def test_identical_consecutive_clicks_on_one_target_are_one() -> None:
    log = [
        *LOGIN,
        _noop_click("Next", url=SITE + "p2", came_from=OVERVIEW),
        _noop_click("Next", url=SITE + "p2", came_from=OVERVIEW),
        READ,
    ]
    assert _clicks(log) == ["Log In", "Next"]


def test_the_menu_links_ordinal_is_counted_on_its_own_look_in_reading_order() -> None:
    """The page heading 'Accounts Overview' sits above the menu link with the same text."""
    items = [
        ("Accounts Overview", Box(20, 262, 160, 278)),  # menu link (OCR returns it first)
        ("Accounts Overview", Box(330, 200, 500, 222)),  # page heading, higher up
        ("Account Services", Box(20, 200, 170, 218)),
    ]
    els = number(items, RefCounter())
    look = Look(b"", b"", els, OVERVIEW)
    link = next(e for e in els if e.box.x1 == 20 and e.text == "Accounts Overview")  # noqa: PLR2004
    assert spot(look, link)["ordinal"] == 2  # noqa: PLR2004
    heading = next(e for e in els if e.box.x1 == 330)  # noqa: PLR2004
    assert spot(look, heading)["ordinal"] == 1


def test_a_scroll_before_a_read_is_kept() -> None:
    log = [*LOGIN, _ev("scroll", {"direction": "down"}, "Scrolled."), READ]
    assert "scroll" in [s.action for s in build_capability(log, _meta(name="r")).steps]


def test_extract_pattern_is_a_regex() -> None:
    assert re.compile(EXTRACT["pattern"])


def test_describe_names_the_capability_after_the_goal() -> None:
    body = inspect.getsource(save.describe)
    assert "after the GOAL" in body
    assert "not the pages" in body

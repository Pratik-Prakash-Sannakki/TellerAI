"""Live: find_accounts_and_transactions.yaml saved `outputs: []`, no extract, and three no-op
steps (click the page it was on, scroll, click it again). A caller got SUCCESS with no data."""
import ast
from dataclasses import dataclass, replace
from pathlib import Path
import re

import pytest

from tests.discovery.test_save_artifact import LOGIN, NS, SENT, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
SITE = "https://parabank.parasoft.com/parabank/"
OVERVIEW = SITE + "overview.htm"


def _click(text: str, result: str = None, url: str = OVERVIEW, came_from: str = OVERVIEW,
           new: bool = True, navigated: bool = True) -> dict:
    """navigated: the page loaded (a link, even back to the same URL); new: new text on screen."""
    return {**_ev("click", {"ref": 3, "x": None, "y": None}, result or f"Clicked {text!r}.",
                  own=text, text=text), "url": url, "from_url": came_from, "loaded": url != came_from,
            "navigated": navigated, "new_texts": new}


READ = {**_ev("extract_value", {"ref": 9, "save_as": "balance", "value_type": "currency",
                                "description": "b"}, "saved", label="Balance*"), "url": OVERVIEW}


def test_a_run_that_neither_reads_nor_sends_is_refused() -> None:
    log = [*LOGIN, _click("Accounts Overview"), _ev("scroll", {"direction": "down"}, "Scrolled.")]
    with pytest.raises(ValueError, match="nothing was read or sent"):
        NS["build_capability"](log, _meta(name="find"))


def test_a_read_or_a_send_is_enough() -> None:
    assert NS["build_capability"]([*LOGIN, READ], _meta(name="r")).outputs[0].name == "balance"
    assert NS["build_capability"]([*LOGIN, SENT], _meta(name="s")).steps


def test_the_live_no_op_clicks_are_dropped() -> None:
    """After login the site is already on Accounts Overview; clicking it, scrolling, clicking it."""
    log = [*LOGIN,
           _click("Accounts Overview", "NO CHANGE after clicking (80, 200). Look again and retry.",
                  new=False),
           _ev("scroll", {"direction": "down"}, "Scrolled."),
           _click("Accounts Overview", new=False), READ]
    steps = NS["build_capability"](log, _meta(name="r")).steps
    assert [s.action for s in steps] == ["type", "type", "click", "extract"]


def test_a_click_that_lands_on_the_page_it_left_is_dropped() -> None:
    log = [*LOGIN, _click("Accounts Overview", new=True), READ]
    clicks = [s for s in NS["build_capability"](log, _meta(name="r")).steps if s.action == "click"]
    assert [c.target.ocr_text.text for c in clicks] == ["Log In"]


def test_a_click_that_changes_the_screen_on_the_same_page_is_kept() -> None:
    log = [*LOGIN, _click("Show details", new=True, navigated=False), READ]
    assert "Show details" in [getattr(s.target.ocr_text, "text", None)
                              for s in NS["build_capability"](log, _meta(name="r")).steps
                              if s.action == "click"]


def test_identical_consecutive_clicks_on_one_target_are_one() -> None:
    log = [*LOGIN, _click("Next", url=SITE + "p2", came_from=OVERVIEW),
           _click("Next", url=SITE + "p2", came_from=OVERVIEW), READ]
    clicks = [s for s in NS["build_capability"](log, _meta(name="r")).steps if s.action == "click"]
    assert [c.target.ocr_text.text for c in clicks] == ["Log In", "Next"]


def test_the_menu_links_ordinal_is_counted_on_its_own_look_in_reading_order() -> None:
    """The page heading 'Accounts Overview' sits above the menu link with the same text."""
    tree = ast.parse(SRC.read_text())
    names = {"Box", "Element", "Look", "number", "spot", "norm"}
    keep = [n for n in tree.body if getattr(n, "name", None) in names
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "REFS")]
    ns: dict = {"dataclass": dataclass, "replace": replace, "re": re, "__name__": "discovery_ord"}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    B = ns["Box"]
    items = [("Accounts Overview", B(20, 262, 160, 278)),       # menu link (OCR returns it first)
             ("Accounts Overview", B(330, 200, 500, 222)),       # page heading, higher up
             ("Account Services", B(20, 200, 170, 218))]
    els = ns["number"](items)
    look = ns["Look"](b"", b"", els, OVERVIEW)
    link = next(e for e in els if e.box.x1 == 20 and e.text == "Accounts Overview")
    assert ns["spot"](look, link)["ordinal"] == 2
    heading = next(e for e in els if e.box.x1 == 330)
    assert ns["spot"](look, heading)["ordinal"] == 1


def test_a_scroll_before_a_read_is_kept() -> None:
    log = [*LOGIN, _ev("scroll", {"direction": "down"}, "Scrolled."), READ]
    assert "scroll" in [s.action for s in NS["build_capability"](log, _meta(name="r")).steps]

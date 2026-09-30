"""Live run 'Log in, bank phone number' (navigate_to_request_loan.yaml): a 404 and detour
navigations were kept, the extract saved a whole sentence, the checkpoint was footer text, and the
name came from the pages visited."""
import ast
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urljoin, urlparse

import pytest

from tests.discovery.test_save_artifact import NS, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
SITE = "https://parabank.parasoft.com/parabank/"
MENU = ["About Us", "Services", "Products", "Locations", "Admin Page", "Account Services"]


def _nav(path: str, status: int = 200, before: list[str] = MENU) -> dict:
    result = f"Opened {path}." if status < 400 else f"HTTP ERROR {status}: {path} does not exist."
    return {**_ev("open_path", {"path": path}, result), "url": SITE + path.lstrip("/"),
            "path": "/parabank/" + path.lstrip("/"), "status": status, "from_texts": before}


def _go(text: str, to: str, before: list[str] = MENU) -> dict:
    return {**_ev("click", {"ref": 3, "x": None, "y": None}, f"Clicked {text!r}.", own=text,
                  text=text), "url": SITE + to, "loaded": True, "from_texts": before}


EXTRACT = {**_ev("extract_value", {"ref": 9, "save_as": "bank_phone_number", "value_type": "phone",
                                   "description": "phone"}, "saved", label="Customer Care"),
           "url": SITE + "about.htm", "pattern": r"\d{3}-\d{3}-\d{4}", "table": None}


def _shapes() -> dict:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) == "value_in_box"
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SHAPES")]
    ns: dict = {"re": re, "value_matches_type": lambda v, t: t == "string" and bool(v.strip())}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def _paths(steps) -> list[str]:
    return [getattr(s, "path", None) or s.target.ocr_text.text for s in steps]


def test_a_404_and_detour_navigations_are_dropped() -> None:
    log = [START, _nav("contact.htm", 404), _nav("contact.htm", 404), _nav("overview.htm"),
           _nav("index.htm"), _go("Contact Us", "contact.htm"), _go("About Us", "about.htm"), EXTRACT]
    steps = NS["build_capability"](log, _meta(name="phone")).steps
    assert _paths(steps[:-1]) == ["About Us"]            # About Us was on the page all along


def test_consecutive_navigations_keep_only_the_last() -> None:
    log = [START, _nav("overview.htm"), _nav("index.htm"), _nav("about.htm"), EXTRACT]
    assert _paths(NS["build_capability"](log, _meta(name="p")).steps[:-1]) == ["/parabank/about.htm"]


def test_a_navigation_needed_to_reach_the_next_link_is_kept() -> None:
    log = [START, _nav("services.htm"), _go("Bookstore", "books.htm", before=["Services", "Bookstore"]),
           EXTRACT]
    log[1]["from_texts"] = MENU                      # 'Bookstore' is only on services.htm
    assert _paths(NS["build_capability"](log, _meta(name="p")).steps[:-1]) == \
        ["/parabank/services.htm", "Bookstore"]


def test_a_click_that_stays_on_the_page_is_never_a_detour() -> None:
    fill = _ev("click", {"ref": 3, "x": None, "y": None}, "Clicked 'Services'.", own="Services",
               text="Services")
    log = [START, fill, _go("About Us", "about.htm"), EXTRACT]
    assert _paths(NS["build_capability"](log, _meta(name="p")).steps[:-1]) == ["Services", "About Us"]


def _open_path(status: int):
    tree = ast.parse(SRC.read_text())
    fn = next(n for n in tree.body if getattr(n, "name", None) == "open_path")
    fn.decorator_list = []
    events = []

    class Page:
        url = SITE

        async def goto(self, url):
            self.url = url
            return SimpleNamespace(status=status)

    async def look():
        return SimpleNamespace(url="u")

    async def reply(msg):
        return msg
    ns = {"urljoin": urljoin, "urlparse": urlparse, "parse_qsl": parse_qsl, "BASE_URL": SITE.rstrip("/"),
          "host_allowed": lambda u: True, "norm": lambda t: t.casefold(), "page": Page(),
          "CFG": SimpleNamespace(deny_words=frozenset()), "take_look": look, "reply": reply,
          "blocks": lambda msg, lk: msg, "page_texts": lambda lk: MENU,
          "HANDOFF": SimpleNamespace(goal="", look=SimpleNamespace()),
          "log": lambda tool, args, result, **extra: events.append({"result": result, **extra})}
    exec(compile(ast.Module([fn], []), str(SRC), "exec"), ns)
    out = asyncio.run(ns["open_path"]("contact.htm"))
    return out, events[-1]


def test_open_path_records_the_http_status_and_the_absolute_path() -> None:
    out, ev = _open_path(404)
    assert ev["status"] == 404 and ev["result"].startswith("HTTP ERROR 404")
    assert ev["path"] == "/parabank/contact.htm" and "does not exist" in out
    assert _open_path(200)[1]["path"] == "/parabank/contact.htm"


def test_a_navigate_step_is_saved_absolute_from_the_origin() -> None:
    log = [START, _nav("about.htm"), EXTRACT]
    assert NS["build_capability"](log, _meta(name="p")).steps[0].path == "/parabank/about.htm"


@pytest.mark.parametrize(("box", "kind", "value", "has_pattern"), [
    ("www.parasoft.com or call 888-305-0041", "phone", "888-305-0041", True),
    ("888-305-0041", "phone", "888-305-0041", False),
    ("Balance: -$202,484.50 today", "currency", "-$202,484.50", True),
    ("-$202484.50", "currency", "-$202484.50", False),
    ("Write to info@parabank.example now", "email", "info@parabank.example", True),
    ("Opened 09/30/2026", "date", "09/30/2026", True),
])
def test_the_value_is_the_first_match_of_its_shape_inside_the_box(box, kind, value, has_pattern) -> None:
    got, pattern = _shapes()["value_in_box"](box, kind)
    assert got == value and (pattern is not None) is has_pattern
    if pattern:
        assert re.search(pattern, box).group() == value and value not in pattern


def test_a_box_without_the_shape_is_refused() -> None:
    assert _shapes()["value_in_box"]("Call us any time", "phone") is None


def test_the_pattern_is_saved_on_the_extract_step_never_the_value() -> None:
    cap = NS["build_capability"]([START, EXTRACT], _meta(name="p"))
    assert cap.steps[0].pattern == r"\d{3}-\d{3}-\d{4}" and cap.outputs[0].type == "phone"
    assert NS["Extract"](target=cap.steps[0].target, save_as="x").pattern is None     # additive


def test_text_on_most_looks_is_never_the_checkpoint() -> None:
    start = {**START, "start_texts": ["Customer Login"], "looks": 4,
             "text_counts": {"parasoft demo website": 4, "about us": 3, "customer care": 1}}
    read = {**EXTRACT, "page_texts": ["ParaSoft Demo Website", "About Us", "Customer Care"]}
    fin = _ev("finish_business_outcome", {"outcome": "x", "proof_text": "ParaSoft Demo Website"}, "OK")
    assert NS["build_capability"]([start, read, fin], _meta(name="p")).checkpoint == "Customer Care"


def test_the_read_pages_heading_is_preferred_over_the_values_label() -> None:
    start = {**START, "start_texts": ["Customer Login"], "looks": 3,
             "text_counts": {"parasoft demo website": 3}}
    read = {**EXTRACT, "page_texts": ["ParaSoft Demo Website", "About Us - ParaBank", "Customer Care"],
            "headings": ["ParaSoft Demo Website", "About Us - ParaBank"]}      # tallest text first
    assert NS["build_capability"]([start, read], _meta(name="p")).checkpoint == "About Us - ParaBank"


def test_describe_names_the_capability_after_the_goal() -> None:
    text = SRC.read_text()
    body = text[text.index("async def describe("):text.index("# %% [markdown]\n# ## Evidence")]
    assert "after the GOAL" in body and "not the pages" in body

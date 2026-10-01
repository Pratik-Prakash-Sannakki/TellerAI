"""Live run 'Log in, bank phone number' (navigate_to_request_loan.yaml): a 404 and detour
navigations were kept, the extract saved a whole sentence, the checkpoint was footer text, and the
name came from the pages visited. The recorder parts moved to
tests/unit/discovery/recorder/test_recorder_runs.py (step 8a); open_path/value_in_box are 8b's."""
import ast
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urljoin, urlparse

import pytest

from tests.discovery.test_save_artifact import _ev

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
SITE = "https://parabank.parasoft.com/parabank/"
MENU = ["About Us", "Services", "Products", "Locations", "Admin Page", "Account Services"]


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



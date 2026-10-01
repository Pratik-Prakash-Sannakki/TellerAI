"""guard_send leftovers: the discovery hook bodies (log_sent_dropdowns, take-over path) and
read_dropdowns. The gates themselves are ported to tests/unit/safety/test_send_guard.py (step 6)."""
import ast
import functools
import json
import re
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlencode, urlparse


SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


async def _no_dropdowns(look, sent) -> None:
    return None


@dataclass
class State:
    entered: dict = field(default_factory=dict)
    allow_send: bool = False
    verdict: str = ""
    goal: str = "transfer $10 from account 14898 to 14898"
    given: list = field(default_factory=list)
    takeover: list | None = None
    look: object = None
    dropdowns: list = field(default_factory=list)
    redact: set = field(default_factory=set)
    log: list = field(default_factory=list)


class Route:
    def __init__(self, method: str) -> None:
        self.request = SimpleNamespace(method=method, url="https://x/services/bank/transfer",
                                       post_data="amount=10&fromAccountId=14898")
        self.outcome, self.sent_body, self.sent_url = "", None, None

    async def continue_(self, url=None, post_data=None) -> None:
        self.outcome, self.sent_body, self.sent_url = "sent", post_data, url

    async def abort(self) -> None:
        self.outcome = "blocked"


class Control:
    def __init__(self, answers, form_answer=None):
        self.answers, self.titles, self.form_answer, self.form_asked = list(answers), [], form_answer, None
        self.images = []

    async def ask(self, title, details, mode, image=None):
        self.titles.append(title)
        self.images.append(image)
        return self.answers.pop(0)

    async def form(self, title, fields, values=None, options=None):
        self.form_asked = (fields, values)
        self.form_options = options
        return self.form_answer


async def _opts(fields, keys):
    return [["1450", "1400"] if fields[k] == "1450" else [] for k in keys]


def test_a_send_during_a_take_over_is_kept_as_its_path_only() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    st, route = State(takeover=[], goal="pay 10 from 13344 to 14898"), Route("POST")
    route.request.url = "https://x/services/bank/billpay?accountId=13344&amount=10"

    async def look():
        return SimpleNamespace(png=b"shot")
    ns = {"HANDOFF": st, "CONTROL": Control(["approve", "approve"]), "SEND_GATE": asyncio.Lock(),
          "take_look": look, "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl,
          "urlencode": urlencode, "re": re, "json": json, "functools": functools,
          "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED",
          "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns,
          "dropdown_options": _opts}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    assert st.takeover == [{"kind": "send", "path": "/services/bank/billpay"}]
    assert "13344" not in str(st.takeover) and "amount" not in str(st.takeover)


class HeldPage:
    """While a request is held, every page read hangs (the live Register bug)."""
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def evaluate(self, *a):
        self.calls.append("evaluate")
        await asyncio.sleep(3600)

    async def screenshot(self, *a, **k):
        self.calls.append("screenshot")
        await asyncio.sleep(3600)


GATE_FNS = {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty",
            "dropdown_options", "log_sent_dropdowns", "is_select", "same_spot", "field_area"}


def _guard_ns(st, ctl, page):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in GATE_FNS]
    logged: list = []
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": page.screenshot,
          "page": page, "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl,
          "urlencode": urlencode, "re": re, "json": json, "functools": functools,
          "is_sensitive": lambda k: "ssn" in k.lower(), "DECLINED": "DECLINED",
          "log": lambda tool, *a, **k: logged.append(tool), "where": lambda look, p: {"label": "From"},
          "cut_crop": lambda *a: b"", "Look": object}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns, logged


def test_a_humans_register_during_a_take_over_needs_no_page_read() -> None:
    """Human values (zip, phone, SSN) are not in the goal: no mismatch form, no dropdown lookup."""
    page = HeldPage()
    st = State(goal="find a way in", takeover=[], look=SimpleNamespace(png=b"old"))
    ctl, route = Control(["approve", "approve"]), Route("POST")
    route.request.url = "https://x/parabank/register.htm"
    route.request.post_data = "customer.address.zipCode=90210&customer.phoneNumber=5551234&customer.ssn=123"
    ns, _ = _guard_ns(st, ctl, page)
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 2))
    assert ctl.titles == ["Gate 1 of 2: confirm the details", "Gate 2 of 2: confirm sending"]
    assert ctl.form_asked is None and page.calls == [] and route.outcome == "sent"
    assert st.takeover == [{"kind": "send", "path": "/parabank/register.htm"}]


def test_an_agent_send_uses_the_stashed_dropdowns_and_never_reads_the_page() -> None:
    page = HeldPage()
    st = State(goal="transfer $10", look=SimpleNamespace(png=b"filled", scale=1.0, url="https://x/t"))
    st.dropdowns = [{"value": "1450", "text": "1450", "options": ["1450", "1400"], "at": [700, 300],
                     "box": [620, 290, 780, 310]}]
    ctl, route = Control(["approve", "approve"], ["1400"]), Route("POST")
    route.request.post_data = "amount=10&fromAccountId=1450"
    ns, logged = _guard_ns(st, ctl, page)
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 2))
    assert ctl.form_options == [["1450", "1400"]]          # the mismatch form, from the stash
    assert "select_option" in logged                        # the sent dropdown is still a step
    assert page.calls == [] and route.outcome == "sent" and "fromAccountId=1400" in route.sent_body


def test_read_dropdowns_on_a_held_page_times_out_to_empty() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) == "read_dropdowns"]
    ns = {"asyncio": asyncio, "page": HeldPage(), "DROPDOWNS_JS": "", "PlaywrightError": RuntimeError,
          "CFG": SimpleNamespace(snap_ms=50)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    assert asyncio.run(asyncio.wait_for(ns["read_dropdowns"](), 2)) == []

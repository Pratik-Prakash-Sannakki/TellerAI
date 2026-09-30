"""guard_send: nothing that sends data leaves the tab without two human approvals."""
import ast
import functools
import json
import re
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlencode, urlparse

import pytest

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


def _run(method, answers, allow=False):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    st, ctl, route = State(allow_send=allow), Control(answers), Route(method)

    async def look():
        return SimpleNamespace(png=b"shot")
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": look,
          "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl, "urlencode": urlencode, "re": re,
          "json": json, "functools": functools,
          "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED",
          "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    return route.outcome, st.verdict, ctl.titles


@pytest.mark.parametrize(("answers", "outcome", "verdict", "asked"), [
    (["approve", "approve"], "sent", "SENT", 2),
    (["approve", "reject"], "blocked", "DECLINED", 2),
    ([None], "blocked", "STUCK", 1),           # control tab closed: fails closed
])
def test_post_needs_two_gates(answers, outcome, verdict, asked) -> None:
    got, v, titles = _run("POST", answers)
    assert got == outcome and v.startswith(verdict) and len(titles) == asked


def test_get_and_login_pass_without_asking() -> None:
    assert _run("GET", [])[0] == "sent"
    assert _run("POST", [], allow=True)[0] == "sent"


def test_sensitive_sent_values_are_masked_in_the_gate() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    seen: list[str] = []

    class Ctl:
        async def ask(self, title, details, mode, image=None):
            seen.append(details)
            return "approve"

    async def look():
        return SimpleNamespace(png=b"shot")
    route = Route("POST")
    route.request.post_data = "user=bob&password=hunter2"
    route.request.url = "https://x/login"
    ns = {"HANDOFF": State(), "CONTROL": Ctl(), "SEND_GATE": asyncio.Lock(), "take_look": look,
          "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl, "urlencode": urlencode, "re": re,
          "json": json, "functools": functools,
          "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED", "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    assert "hunter2" not in seen[0] and "Password: ******" in seen[0] and "User: bob" in seen[0]


async def _opts(fields, keys):
    return [["1450", "1400"] if fields[k] == "1450" else [] for k in keys]


def _send(post_data: str, goal: str, given: list[str], form_answer=None):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    st, ctl, route = State(goal=goal, given=given), Control(["approve", "approve"], form_answer), Route("POST")
    route.request.post_data = post_data

    async def look():
        return SimpleNamespace(png=b"shot")
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": look,
          "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl, "re": re,
          "urlencode": urlencode, "json": json, "functools": functools, "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED",
          "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns, "dropdown_options": _opts}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    return route, st.verdict, ctl


def test_default_dropdown_is_asked_in_the_form_and_the_answer_is_sent() -> None:
    """The user's case: a dropdown kept its default (1450), the human never gave it."""
    route, verdict, ctl = _send("amount=10&fromAccountId=1450", "transfer $10", [], ["1400"])
    assert ctl.form_asked == ([("From account id", False)], ["1450"])    # prefilled with the default
    assert ctl.form_options == [["1450", "1400"]]                         # and shows the choices
    assert route.outcome == "sent" and "fromAccountId=1400" in route.sent_body
    assert ctl.titles == ["Gate 1 of 2: confirm the details", "Gate 2 of 2: confirm sending"]


def test_skipping_the_form_blocks_the_send() -> None:
    route, verdict, ctl = _send("amount=10&fromAccountId=1450", "transfer $10", [], None)
    assert route.outcome == "blocked" and verdict.startswith("STUCK") and ctl.titles == []


def test_matching_values_go_straight_to_confirmation_gates() -> None:
    route, verdict, ctl = _send("amount=10.00&fromAccountId=1400", "transfer $10", ["1400"])
    assert route.outcome == "sent" and ctl.form_asked is None and verdict.startswith("SENT")


def test_gate1_edit_goes_back_to_the_form_and_sends_the_edit() -> None:
    """Gate 1 = Approve / Edit. Edit reopens the form with every value; the edit is what is sent."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    st = State(goal="transfer $10", given=["1400"], look=SimpleNamespace(png=b"shot"))
    ctl = Control(["edit", "approve", "approve"], ["25", "1400"])
    route = Route("POST")
    route.request.post_data = "amount=10&fromAccountId=1400"

    async def look():
        return SimpleNamespace(png=b"shot")
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": look,
          "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl, "re": re,
          "urlencode": urlencode, "json": json, "functools": functools, "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED",
          "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns, "dropdown_options": _opts}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    assert ctl.form_asked == ([("Amount", False), ("From account id", False)], ["10", "1400"])
    assert route.outcome == "sent" and "amount=25" in route.sent_body
    assert ctl.titles == ["Gate 1 of 2: confirm the details", "Gate 1 of 2: confirm the details",
                          "Gate 2 of 2: confirm sending"]
    assert ctl.images == [b"shot", None, None]     # the old screenshot is gone once values change


def test_bill_pay_json_every_field_is_editable_and_sent_back_as_json() -> None:
    """The user's case: Bill Pay sends JSON (payee in the body, account + amount in the URL), and
    Edit only showed accountId + amount. Every field must show, and an edit go out as JSON."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in
            {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    body = json.dumps({"name": "Acme", "address": {"street": "1 Main", "city": "Troy", "zipCode": "12180"},
                       "phoneNumber": "5551234", "accountNumber": 777})
    given = ["124677", "2", "1", "12180", "5551234", "777"]
    st = State(goal="pay a bill", given=given)
    names = ["Account id", "Amount", "Name", "Address street", "Address city", "Address zip code",
             "Phone number", "Account number"]
    edited = ["124677", "2", "Acme Power", "1 Main", "Troy", "12180", "5551234", "777"]
    ctl = Control(["edit", "approve", "approve"], edited)
    route = Route("POST")
    route.request.url = "https://x/services/bank/billpay?accountId=124677&amount=2"
    route.request.post_data = body

    async def look():
        return SimpleNamespace(png=b"shot")
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": look,
          "hide_secrets": lambda t: t, "urlparse": urlparse, "parse_qsl": parse_qsl, "re": re,
          "urlencode": urlencode, "json": json, "functools": functools,
          "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED",
          "log": lambda *a, **k: None, "log_sent_dropdowns": _no_dropdowns, "dropdown_options": _opts}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["guard_send"](route))
    assert [f for f, _ in ctl.form_asked[0]] == names                       # every field, readable
    assert route.outcome == "sent"
    sent = json.loads(route.sent_body)
    assert sent["name"] == "Acme Power" and sent["address"]["city"] == "Troy"
    assert sent["accountNumber"] == 777                                   # number stays a number


def test_only_the_real_dropdown_becomes_a_dropdown() -> None:
    """The user's screenshot: every field set to "1", amount 124677, one real dropdown holding
    14898/124677. Amount and State must stay text boxes; only Account id gets the options."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) == "dropdown_options"
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DROPDOWNS_JS")]

    stash = [{"value": "14898", "text": "14898", "options": ["14898", "124677"]}]
    ns = {"HANDOFF": SimpleNamespace(dropdowns=stash), "hide_secrets": lambda t: t}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    fields = {"accountId": "14898", "amount": "124677", "address.street": "1", "address.state": "1",
              "name": "1"}
    got = asyncio.run(ns["dropdown_options"](fields, list(fields)))
    assert got == [["14898", "124677"], [], [], [], []]


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


def _held_navigation(takeover):
    """A form POST (Register) is a navigation: the page cannot screenshot while it is held."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"guard_send", "mismatches", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}]
    st = State(goal="register", takeover=takeover, look=SimpleNamespace(png=b"last look"))
    ctl, route = Control(["approve", "approve"]), Route("POST")
    route.request.post_data = "customer.firstName=Ann"
    route.request.is_navigation_request = lambda: True

    async def never(*a, **k):
        raise AssertionError("screenshot while a navigation is held: it would hang")
    ns = {"HANDOFF": st, "CONTROL": ctl, "SEND_GATE": asyncio.Lock(), "take_look": never,
          "page": SimpleNamespace(screenshot=never), "hide_secrets": lambda t: t, "urlparse": urlparse,
          "parse_qsl": parse_qsl, "urlencode": urlencode, "re": re, "json": json, "functools": functools,
          "is_sensitive": lambda k: "password" in k, "DECLINED": "DECLINED", "log": lambda *a, **k: None,
          "log_sent_dropdowns": _no_dropdowns, "dropdown_options": _opts}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 2))
    return route, ctl


def test_a_held_navigation_never_screenshots_and_the_gate_shows() -> None:
    route, ctl = _held_navigation(takeover=[])
    assert ctl.titles == ["Gate 1 of 2: confirm the details", "Gate 2 of 2: confirm sending"]
    assert ctl.images == [None, None]         # a human's send: no current look, so no image
    assert route.outcome == "sent"


def test_the_agents_own_send_shows_its_last_look() -> None:
    _, ctl = _held_navigation(takeover=None)
    assert ctl.images == [b"last look", b"last look"]


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


def test_a_humans_edit_at_gate1_uses_plain_fields() -> None:
    page = HeldPage()
    st = State(goal="x", takeover=[])
    ctl, route = Control(["edit", "approve", "approve"], ["1400", "10"]), Route("POST")
    ns, _ = _guard_ns(st, ctl, page)
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 2))
    assert ctl.form_options == [[], []] and page.calls == [] and route.outcome == "sent"


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

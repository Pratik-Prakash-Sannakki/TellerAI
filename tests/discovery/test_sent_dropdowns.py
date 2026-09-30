"""A dropdown the send carries becomes a Select step, even when left on its page default."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import yaml

from tests.discovery.test_save_artifact import LOGIN, NS, SENT, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
ACCOUNT = "74838"
BILLPAY = "https://parabank.parasoft.com/parabank/billpay.htm"


def _logged(sent: dict) -> list[dict]:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in
            {"log_sent_dropdowns", "is_select", "field_area", "same_spot"}
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FIELD_GAP")]
    events: list[dict] = []

    class Page:
        async def evaluate(self, js):
            raise AssertionError("page read while a send is held: it would hang")

    stash = [{"value": ACCOUNT, "text": ACCOUNT, "options": [ACCOUNT, "13344"], "at": [720, 540],
              "box": [640, 530, 800, 550]},
             {"value": "x", "text": "x", "options": ["x"], "at": None, "box": [0, 0, 0, 0]}]         # hidden: skipped

    def where(look, point):
        return {"own": None, "anchor": {"text": "From account #:", "box": [480, 530, 590, 550],
                                        "ordinal": 1}, "label": "From account #:", "offset": [185, 0]}

    ns = {"DROPDOWNS_JS": "", "page": Page(), "HANDOFF": SimpleNamespace(dropdowns=stash, log=[]), "urlparse": urlparse, "where": where, "cut_crop": lambda *a: b"crop", "Look": object,
          "log": lambda tool, args, result, point=None, crop=None, **extra: events.append(
              {"tool": tool, "args": args, "result": result, "point": point, "crop": crop,
               "url": BILLPAY, **extra})}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["log_sent_dropdowns"](SimpleNamespace(scale=1.0, url=BILLPAY), sent))
    return events


def test_a_defaulted_dropdown_the_send_carries_is_logged_without_its_value() -> None:
    events = _logged({"amount": "10", "fromAccountId": ACCOUNT})
    assert len(events) == 1 and events[0]["point"] == (720, 540)
    assert events[0]["args"] == {"hint": "From account #:"} and events[0]["dropdown"] is True
    assert ACCOUNT not in str(events[0])


def test_a_dropdown_the_send_does_not_carry_is_not_a_step() -> None:
    assert _logged({"amount": "10"}) == []


def test_it_becomes_a_select_input_before_the_send_click(tmp_path: Path) -> None:
    log = [*LOGIN,
           _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).", label="Amount:"),
           *_logged({"amount": "10", "fromAccountId": ACCOUNT}), SENT,
           _ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Send Payment'.", label="Amount:",
               own="Send Payment", text="Send Payment", landed=["Bill Payment Complete"])]
    cap = NS["build_capability"](log, _meta(name="pay"))
    acts = [s.action for s in cap.steps]
    assert acts[-2:] == ["select", "click"]
    assert cap.steps[-2].option == "{{from_account}}"
    assert cap.steps[-2].target.anchor.label == "From account #:"
    assert "from_account" in [i.name for i in cap.inputs]
    path = NS["save_artifact"](cap, NS["crops_for"](log, cap), tmp_path)
    assert ACCOUNT not in path.read_text()
    assert yaml.safe_load(path.read_text())["steps"][-2]["action"] == "select"


def test_a_select_the_agent_made_earlier_is_not_doubled() -> None:
    early = {**_logged({"a": ACCOUNT})[0], "tool": "select_option", "args": {"ref": 5, "x": None, "y": None}}
    log = [START, early, *_logged({"a": ACCOUNT}), SENT,
           _ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Send'.", own="Send", text="Send",
               landed=["Done"])]
    assert [s.action for s in NS["build_capability"](log, _meta(name="pay")).steps] == ["select", "click"]

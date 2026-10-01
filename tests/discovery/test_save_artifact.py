"""Shared notebook fixtures (NS, LOGIN, SENT, START, PAY, _ev, _meta) and the `_look_ns` tests.

The recorder tests were ported to tests/unit/discovery/recorder/ (step 3). The fixtures stay
because other old tests import them; where/label_near/spot are not ported yet.
"""
import ast
import re
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qsl, urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
TEXT = SRC.read_text()
LINES = TEXT.splitlines()


def _section() -> dict:
    """Every cell of '## Save artifact', plus the helpers it uses from earlier cells."""
    start = LINES.index("# ## Save artifact")
    end = LINES.index("# ## Run")
    tree = ast.parse(TEXT)
    helpers = {"FAILED", "norm", "flag_leaks", "redactor", "_num", "NUMBER", "is_select",
               "field_area", "same_spot", "FIELD_GAP"}
    keep = [n for n in tree.body if start < n.lineno < end
            or getattr(n, "name", None) in helpers
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in helpers)]
    ns: dict = {"__name__": "discovery_save", "re": re, "Path": Path, "Annotated": Annotated, "Literal": Literal, "yaml": yaml,
                "urlparse": urlparse, "parse_qsl": parse_qsl, "BaseModel": BaseModel, "ConfigDict": ConfigDict,
                "Field": Field, "model_validator": model_validator}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


NS = _section()
PNG = b"\x89PNG fake"
START = {"tool": "start", "args": {"base_url": "https://parabank.parasoft.com/parabank",
                                   "viewport": [1280, 800], "device_scale_factor": 1},
         "result": "run started", "point": None, "url": "https://parabank.parasoft.com/parabank/",
         "crop": None}


def _ev(tool: str, args: dict, result: str, label: str | None = None, own: str | None = None,
        **extra) -> dict:
    ev = {"tool": tool, "args": args, "result": result, "point": (300, 200),
          "url": "https://parabank.parasoft.com/parabank/index.htm", "crop": PNG, **extra}
    if label:
        ev["anchor"] = {"text": label, "box": [100, 190, 180, 210], "ordinal": 1}
        ev["offset"] = [160, 0]
        ev["label"] = label
    if own:
        ev["own"] = {"text": own, "box": [280, 190, 320, 210], "ordinal": 1}
    return ev


SENT = {"tool": "send", "args": {"path": "/parabank/services/bank/transfer"}, "result": "approved by human",
        "point": None, "url": "https://parabank.parasoft.com/parabank/transfer.htm", "crop": None}
"""A send a human approved: not a step, but what makes a run worth saving. Step-shape tests add
it so they test step building, not build_capability's 'nothing was read or sent' refusal."""

LOGIN = [START,
         _ev("type_secret", {"secret_name": "username"}, "Typed secret 'username' at (300, 200).",
             label="Username"),
         _ev("type_secret", {"secret_name": "password"}, "Typed secret 'password' at (300, 230).",
             label="Password"),
         _ev("click", {"ref": 7, "x": None, "y": None}, "Clicked 'Log In'.", label="Log In",
             own="Log In", text="Log In")]


def _meta(**kw):
    return NS["CapabilityMeta"](**{"name": "login", "description": "Log in.",
                                   "success_text": "Accounts Overview", **kw})


def _look_ns() -> dict:
    tree = ast.parse(TEXT)
    names = {"Box", "Element", "Look", "element_at", "label_near", "spot", "where", "merged_label", "norm",
             "clean_label", "redactor", "_num"}
    keep = [n for n in tree.body if getattr(n, "name", None) in names
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NUMBER")]
    from dataclasses import dataclass, replace
    ns: dict = {"dataclass": dataclass, "replace": replace, "re": re, "run_values": set,
                "__name__": "discovery_where"}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def test_where_records_label_box_ordinal_offset_but_not_the_box_contents() -> None:
    ns = _look_ns()
    B, E = ns["Box"], ns["Element"]
    els = (E(1, "Amount:", B(10, 10, 70, 30)), E(2, "Amount:", B(10, 60, 70, 80)),
           E(3, "4242", B(100, 60, 160, 80)))     # a value already in the box
    look = ns["Look"](b"", b"", els, "u")
    got = ns["where"](look, (130, 70))
    assert got["label"] == "Amount:" and got["anchor"]["ordinal"] == 2
    assert got["anchor"]["box"] == [10, 60, 70, 80] and got["offset"] == [90, 0]
    assert "4242" not in str(got)


def test_a_dropdowns_own_number_is_never_its_label() -> None:
    """Live bug: 'From account #' dropdown showing '74838' was saved as input 'f_74838'."""
    ns = _look_ns()
    B, E = ns["Box"], ns["Element"]
    els = (E(1, "From account #:", B(10, 60, 120, 80)), E(2, "74838", B(200, 60, 250, 80)))
    look = ns["Look"](b"", b"", els, "u")
    got = ns["where"](look, (270, 70))          # just right of the value, inside the dropdown
    assert got["label"] == "From account #:"


PAY = [*LOGIN,
       _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).", label="Amount"),
       _ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Send Payment'.", label="Amount",
           own="Send Payment", text="Send Payment", landed=["Bill Payment Complete", "See Account Activity"]),
       SENT,
       _ev("finish_business_outcome", {"outcome": "paid", "proof_text": "Request Loan"}, "OK"),
       _ev("scroll", {"direction": "down"}, "Scrolled."),
       _ev("click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", label="Request Loan",
           own="Log Out", text="Log Out")]


def test_a_typed_value_above_is_never_the_next_fields_label() -> None:
    """Live bug: 'Sean' typed into Payee Name became the Address step's label and input name."""
    ns = _look_ns()
    B, E = ns["Box"], ns["Element"]
    els = (E(1, "Payee Name:", B(10, 10, 110, 30)), E(2, "Sean", B(200, 10, 240, 30)),
           E(3, "Address:", B(10, 40, 80, 60)))
    look = ns["Look"](b"", b"", els, "u")
    assert ns["where"](look, (250, 50))["label"] == "Address:"                  # same row wins
    assert ns["label_near"](look, (250, 75), avoid={"sean"}).text == "Address:"  # a value is never one



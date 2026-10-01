"""Shared notebook fixtures (NS, LOGIN, SENT, START, PAY, _ev, _meta) and the `_look_ns` tests.

The recorder tests were ported to tests/unit/discovery/recorder/ (step 3). The fixtures stay
because other old tests import them. The `_look_ns` tests moved to
tests/unit/discovery/tools/test_read_helpers.py (step 8a).
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


PAY = [*LOGIN,
       _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).", label="Amount"),
       _ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Send Payment'.", label="Amount",
           own="Send Payment", text="Send Payment", landed=["Bill Payment Complete", "See Account Activity"]),
       SENT,
       _ev("finish_business_outcome", {"outcome": "paid", "proof_text": "Request Loan"}, "OK"),
       _ev("scroll", {"direction": "down"}, "Scrolled."),
       _ev("click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", label="Request Loan",
           own="Log Out", text="Log Out")]



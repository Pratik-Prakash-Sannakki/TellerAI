"""Save artifact: the event log becomes a replay-ready capability (R12, R13, R16). No values stored."""
import ast
import re
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qsl, urlparse

import pytest
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
    helpers = {"FAILED", "norm", "flag_leaks"}
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


def test_login_becomes_three_steps_with_anchors_and_secret_refs() -> None:
    cap = NS["build_capability"](LOGIN, _meta())
    assert [s.action for s in cap.steps] == ["type", "type", "click"]
    assert cap.steps[0].value == "{{secret:username}}"
    assert cap.steps[1].value == "{{secret:password}}"
    assert cap.steps[0].target.anchor.label == "Username"
    assert tuple(cap.steps[0].target.anchor.offset) == (160, 0)
    assert cap.steps[2].target.ocr_text.text == "Log In"
    assert cap.steps[2].target.template == "crops/login/s2.png"
    assert cap.secrets == ["username", "password"]
    assert tuple(cap.viewport) == (1280, 800) and cap.schema_version == 2


def test_failed_then_successful_type_text_is_one_input_step() -> None:
    log = [START,
           _ev("type_text", {"ref": 3, "x": None, "y": None}, "TYPED at (300, 200) but the box shows ''.",
               label="Amount"),
           _ev("type_text", {"ref": 4, "x": None, "y": None}, "Typed at (300, 200).",
               label="Amount")]
    cap = NS["build_capability"](log, _meta(name="pay"))
    assert len(cap.steps) == 1
    assert cap.steps[0].value == "{{amount}}"
    assert [i.name for i in cap.inputs] == ["amount"]


def test_human_entry_becomes_input_named_from_its_label() -> None:
    log = [START, _ev("request_value", {"hint": "Zip Code:"}, "human entry", label="Zip Code:",
                      human_entry=True, dropdown=False)]
    cap = NS["build_capability"](log, _meta(name="pay"))
    assert cap.steps[0].action == "type" and cap.steps[0].value == "{{zip_code}}"
    assert cap.inputs[0].name == "zip_code"


def test_take_over_refuses() -> None:
    log = [*LOGIN, _ev("take_over", {"reason": "x"}, "handed back", human_entry=True,
                       recordable=False)]
    with pytest.raises(ValueError, match="take-over"):
        NS["build_capability"](log, _meta())


def test_model_cannot_break_the_build() -> None:
    """Invented inputs are ignored, a missing description gets a default, secrets stay refs."""
    log = [*LOGIN, _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).",
                       label="Zip Code:")]
    meta = _meta(name="Log In Flow", inputs={"customer_login": "user id", "password": "pw"})
    cap = NS["build_capability"](log, meta)
    assert [i.name for i in cap.inputs] == ["zip_code"]
    assert cap.inputs[0].description == "zip code"
    assert [s.value for s in cap.steps if s.action == "type"] == [
        "{{secret:username}}", "{{secret:password}}", "{{zip_code}}"]
    assert cap.name == "log_in_flow" and cap.steps[0].target.template == "crops/log_in_flow/s0.png"


def test_used_inputs_skips_secrets() -> None:
    log = [*LOGIN, _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed.", label="Amount")]
    assert NS["used_inputs"](log) == ["amount"]


def test_save_round_trips_and_holds_no_typed_value(tmp_path: Path) -> None:
    typed = "90210-secret-value"          # what the human/agent typed: never in the log, never saved
    log = [*LOGIN, _ev("request_value", {"hint": "Zip Code:"}, "human entry", label="Zip Code:",
                       human_entry=True, dropdown=False),
           _ev("extract_value", {"ref": 9, "save_as": "first_balance", "value_type": "currency",
                                 "description": "Balance"}, "saved", label="Balance",
               table={"row_key": "13344", "column": "Balance"})]
    cap = NS["build_capability"](log, _meta())
    path = NS["save_artifact"](cap, NS["crops_for"](log, cap), tmp_path)
    again = NS["Capability"].model_validate(yaml.safe_load(path.read_text()))
    assert again == cap
    assert (tmp_path / "crops/login/s0.png").read_bytes() == PNG
    assert typed not in path.read_text()
    assert again.steps[-1].target.template is None       # an extract crop shows the value: not saved
    assert again.outputs[0].name == "first_balance"


def test_same_field_typed_twice_keeps_the_last() -> None:
    first = _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).", label="Amount")
    again = {**_ev("type_text", {"ref": 5, "x": None, "y": None}, "Typed at (300, 200).",
                   label="Amount"), "crop": b"second"}
    cap = NS["build_capability"]([START, first, again], _meta(name="pay"))
    assert len(cap.steps) == 1
    assert NS["crops_for"]([START, first, again], cap) == {"crops/pay/s0.png": b"second"}


def test_open_path_query_values_become_inputs() -> None:
    log = [START, _ev("open_path", {"path": "activity.htm?id=13344"}, "Opened activity.htm?id=13344.")]
    cap = NS["build_capability"](log, _meta(name="acct"))
    assert cap.steps[0].path == "/activity.htm?id={{id}}"
    assert [i.name for i in cap.inputs] == ["id"]


def _look_ns() -> dict:
    tree = ast.parse(TEXT)
    names = {"Box", "Element", "Look", "element_at", "label_near", "spot", "where", "norm"}
    keep = [n for n in tree.body if getattr(n, "name", None) in names]
    from dataclasses import dataclass
    ns: dict = {"dataclass": dataclass, "re": re, "run_values": set, "__name__": "discovery_where"}
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
       _ev("finish_business_outcome", {"outcome": "paid", "proof_text": "Request Loan"}, "OK"),
       _ev("scroll", {"direction": "down"}, "Scrolled."),
       _ev("click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", label="Request Loan",
           own="Log Out", text="Log Out")]


def test_trailing_logout_and_scroll_are_not_steps() -> None:
    cap = NS["build_capability"](PAY, _meta(name="pay"))
    assert cap.steps[-1].action == "click" and cap.steps[-1].target.ocr_text.text == "Send Payment"
    assert len(NS["crops_for"](PAY, cap)) == len(cap.steps)


def test_checkpoint_after_a_send_is_the_pages_response_not_a_nav_link() -> None:
    cap = NS["build_capability"](PAY, _meta(name="pay", success_text="Request Loan"))
    assert cap.checkpoint == "Bill Payment Complete"


def test_a_proof_inside_the_response_is_kept() -> None:
    log = [*PAY[:-3], _ev("finish_business_outcome", {"outcome": "paid",
                                                       "proof_text": "Payment Complete"}, "OK")]
    assert NS["build_capability"](log, _meta(name="pay")).checkpoint == "Payment Complete"


def test_a_lone_logout_is_still_a_step() -> None:
    log = [START, _ev("click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", own="Log Out",
                      text="Log Out")]
    assert len(NS["build_capability"](log, _meta(name="bye")).steps) == 1


def test_a_typed_value_above_is_never_the_next_fields_label() -> None:
    """Live bug: 'Sean' typed into Payee Name became the Address step's label and input name."""
    ns = _look_ns()
    B, E = ns["Box"], ns["Element"]
    els = (E(1, "Payee Name:", B(10, 10, 110, 30)), E(2, "Sean", B(200, 10, 240, 30)),
           E(3, "Address:", B(10, 40, 80, 60)))
    look = ns["Look"](b"", b"", els, "u")
    assert ns["where"](look, (250, 50))["label"] == "Address:"                  # same row wins
    assert ns["label_near"](look, (250, 75), avoid={"sean"}).text == "Address:"  # a value is never one


def test_save_refuses_a_step_whose_label_is_a_typed_value() -> None:
    log = [*LOGIN, _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed.", label="Sean")]
    NS["flag_leaks"](log, {"sean"})
    with pytest.raises(ValueError, match="value typed this run") as err:
        NS["build_capability"](log, _meta(name="pay"))
    assert "sean" not in str(err.value).casefold()
    assert all(k != "value" for ev in log for k in ev)                    # nothing but a flag stored


def test_flag_leaks_leaves_clean_events_alone() -> None:
    log = [*LOGIN, _ev("type_text", {"ref": 3, "x": None, "y": None}, "Typed.", label="Address:")]
    NS["flag_leaks"](log, {"sean"})
    assert not any(ev.get("leak") for ev in log)


def test_save_still_refuses_a_run_with_a_take_over_that_has_evidence() -> None:
    ev = _ev("take_over", {"reason": "x"}, "handed back", human_entry=True, recordable=False,
             actions=[{"kind": "page", "path": "/parabank/billpay.htm"}],
             shot_before=PNG, shot_after=PNG)
    with pytest.raises(ValueError, match="take-over"):
        NS["build_capability"]([*LOGIN, ev], _meta())

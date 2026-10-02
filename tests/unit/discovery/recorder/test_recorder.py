"""The recorder: the event log becomes a replay-ready capability (R12, R13, R16). No values stored.

Ported from tests/discovery/test_save_artifact.py (all but its ``_look_ns`` tests, whose code is
not in cua.discovery.recorder yet), now importing the package instead of exec'ing the notebook.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cua.discovery.recorder import (
    build_capability,
    crops_for,
    describe,
    flag_leaks,
    input_name,
    is_select,
    same_spot,
    save_artifact,
    step_events,
    used_inputs,
)
from cua.schema import Capability, CapabilityMeta

PNG = b"\x89PNG fake"
START = {
    "tool": "start",
    "args": {
        "base_url": "https://parabank.parasoft.com/parabank",
        "viewport": [1280, 800],
        "device_scale_factor": 1,
    },
    "result": "run started",
    "point": None,
    "url": "https://parabank.parasoft.com/parabank/",
    "crop": None,
}


def _ev(
    tool: str, args: dict, result: str, label: str | None = None, own: str | None = None, **extra
) -> dict:
    ev = {
        "tool": tool,
        "args": args,
        "result": result,
        "point": (300, 200),
        "url": "https://parabank.parasoft.com/parabank/index.htm",
        "crop": PNG,
        **extra,
    }
    if label:
        ev["anchor"] = {"text": label, "box": [100, 190, 180, 210], "ordinal": 1}
        ev["offset"] = [160, 0]
        ev["label"] = label
    if own:
        ev["own"] = {"text": own, "box": [280, 190, 320, 210], "ordinal": 1}
    return ev


REF = {"ref": 3, "x": None, "y": None}
SENT = {
    "tool": "send",
    "args": {"path": "/parabank/services/bank/transfer"},
    "result": "approved by human",
    "point": None,
    "url": "https://parabank.parasoft.com/parabank/transfer.htm",
    "crop": None,
}
"""A send a human approved: not a step, but what makes a run worth saving."""

LOGIN = [
    START,
    _ev("type_secret", {"secret_name": "username"}, "Typed secret 'username'.", label="Username"),
    _ev("type_secret", {"secret_name": "password"}, "Typed secret 'password'.", label="Password"),
    _ev(
        "click",
        {"ref": 7, "x": None, "y": None},
        "Clicked 'Log In'.",
        "Log In",
        "Log In",
        text="Log In",
    ),
]


def _meta(**kw: object) -> CapabilityMeta:
    base = {"name": "login", "description": "Log in.", "success_text": "Accounts Overview"}
    return CapabilityMeta(**{**base, **kw})


def test_login_becomes_three_steps_with_anchors_and_secret_refs() -> None:
    cap = build_capability([*LOGIN, SENT], _meta())
    assert [s.action for s in cap.steps] == ["type", "type", "click"]
    assert cap.steps[0].value == "{{secret:username}}"
    assert cap.steps[1].value == "{{secret:password}}"
    assert cap.steps[0].target.anchor.label == "Username"
    assert tuple(cap.steps[0].target.anchor.offset) == (160, 0)
    assert cap.steps[2].target.ocr_text.text == "Log In"
    assert cap.steps[2].target.template == "crops/login/s2.png"
    assert cap.secrets == ["username", "password"]
    assert tuple(cap.viewport) == (1280, 800)
    assert cap.schema_version == 2  # noqa: PLR2004


def test_failed_then_successful_type_text_is_one_input_step() -> None:
    log = [
        START,
        _ev("type_text", REF, "TYPED at (300, 200) but the box shows ''.", label="Amount"),
        _ev("type_text", {**REF, "ref": 4}, "Typed at (300, 200).", label="Amount"),
        SENT,
    ]
    cap = build_capability(log, _meta(name="pay"))
    assert len(cap.steps) == 1
    assert cap.steps[0].value == "{{amount}}"
    assert [i.name for i in cap.inputs] == ["amount"]


def test_human_entry_becomes_input_named_from_its_label() -> None:
    entry = _ev(
        "request_value",
        {"hint": "Zip Code:"},
        "human entry",
        label="Zip Code:",
        human_entry=True,
        dropdown=False,
    )
    cap = build_capability([START, entry, SENT], _meta(name="pay"))
    assert cap.steps[0].action == "type"
    assert cap.steps[0].value == "{{zip_code}}"
    assert cap.inputs[0].name == "zip_code"


def test_take_over_refuses() -> None:
    ev = _ev("take_over", {"reason": "x"}, "handed back", human_entry=True, recordable=False)
    with pytest.raises(ValueError, match="take-over"):
        build_capability([*LOGIN, ev], _meta())


def test_model_cannot_break_the_build() -> None:
    """Invented inputs are ignored, a missing description gets a default, secrets stay refs."""
    log = [*LOGIN, _ev("type_text", REF, "Typed at (300, 200).", label="Zip Code:"), SENT]
    meta = _meta(name="Log In Flow", inputs={"customer_login": "user id", "password": "pw"})
    cap = build_capability(log, meta)
    assert [i.name for i in cap.inputs] == ["zip_code"]
    assert cap.inputs[0].description == "zip code"
    assert [s.value for s in cap.steps if s.action == "type"] == [
        "{{secret:username}}",
        "{{secret:password}}",
        "{{zip_code}}",
    ]
    assert cap.name == "log_in_flow"
    assert cap.steps[0].target.template == "crops/log_in_flow/s0.png"


def test_used_inputs_skips_secrets() -> None:
    log = [*LOGIN, _ev("type_text", REF, "Typed.", label="Amount")]
    assert used_inputs(log) == ["amount"]


def test_save_round_trips_and_holds_no_typed_value(tmp_path: Path) -> None:
    typed = "90210-secret-value"  # what the human/agent typed: never in the log, never saved
    log = [
        *LOGIN,
        _ev(
            "request_value",
            {"hint": "Zip Code:"},
            "human entry",
            label="Zip Code:",
            human_entry=True,
            dropdown=False,
        ),
        _ev(
            "extract_value",
            {
                "ref": 9,
                "save_as": "first_balance",
                "value_type": "currency",
                "description": "Balance",
            },
            "saved",
            label="Balance",
            table={"row_key": "13344", "column": "Balance"},
        ),
    ]
    cap = build_capability(log, _meta())
    path = save_artifact(cap, crops_for(log, cap), tmp_path)
    again = Capability.model_validate(yaml.safe_load(path.read_text()))
    assert again == cap
    assert (tmp_path / "crops/login/s0.png").read_bytes() == PNG
    assert typed not in path.read_text()
    assert again.steps[-1].target.template is None  # an extract crop shows the value: not saved
    assert again.outputs[0].name == "first_balance"


def test_save_artifact_defaults_to_top_level_artifacts() -> None:
    """User decision 6: artifacts/<name>.yaml + artifacts/crops/<name>/ (was artifacts/visual)."""
    assert save_artifact.__defaults__ == (Path("artifacts"),)


def test_same_field_typed_twice_keeps_the_last() -> None:
    first = _ev("type_text", REF, "Typed at (300, 200).", label="Amount")
    again = {
        **_ev("type_text", {**REF, "ref": 5}, "Typed at (300, 200).", label="Amount"),
        "crop": b"second",
    }
    cap = build_capability([START, first, again, SENT], _meta(name="pay"))
    assert len(cap.steps) == 1
    assert crops_for([START, first, again, SENT], cap) == {"crops/pay/s0.png": b"second"}


def test_open_path_query_values_become_inputs() -> None:
    nav = _ev("open_path", {"path": "activity.htm?id=13344"}, "Opened activity.htm?id=13344.")
    cap = build_capability([START, nav, SENT], _meta(name="acct"))
    assert cap.steps[0].path == "/activity.htm?id={{id}}"
    assert [i.name for i in cap.inputs] == ["id"]


PAY = [
    *LOGIN,
    _ev("type_text", REF, "Typed at (300, 200).", label="Amount"),
    _ev(
        "click",
        {"ref": 8, "x": None, "y": None},
        "Clicked 'Send Payment'.",
        "Amount",
        "Send Payment",
        text="Send Payment",
        landed=["Bill Payment Complete", "See Account Activity"],
    ),
    SENT,
    _ev("finish_business_outcome", {"outcome": "paid", "proof_text": "Request Loan"}, "OK"),
    _ev("scroll", {"direction": "down"}, "Scrolled."),
    _ev(
        "click",
        {"ref": 9, "x": None, "y": None},
        "Clicked 'Log Out'.",
        "Request Loan",
        "Log Out",
        text="Log Out",
    ),
]
LOGOUT = _ev(
    "click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", own="Log Out", text="Log Out"
)


def test_the_trailing_logout_is_kept_last_as_cleanup_and_the_scroll_dropped() -> None:
    """Banking safety (user, 2026-09-29): replay ends logged out."""
    cap = build_capability(PAY, _meta(name="pay"))
    *work, last = cap.steps
    assert last.action == "click"
    assert last.target.ocr_text.text == "Log Out"
    assert last.cleanup is True
    assert work[-1].target.ocr_text.text == "Send Payment"
    assert work[-1].cleanup is False
    assert "scroll" not in [s.action for s in cap.steps]
    assert len(crops_for(PAY, cap)) == len(cap.steps)


def test_only_the_last_of_repeated_logout_clicks_is_kept() -> None:
    steps = build_capability([*PAY, LOGOUT], _meta(name="pay")).steps
    assert [s.cleanup for s in steps if s.action == "click"][-2:] == [False, True]


def test_the_cleanup_flag_survives_the_saved_yaml(tmp_path: Path) -> None:
    cap = build_capability(PAY, _meta(name="pay"))
    path = save_artifact(cap, crops_for(PAY, cap), tmp_path)
    saved = yaml.safe_load(path.read_text())["steps"]
    assert saved[-1]["cleanup"] is True
    assert Capability.model_validate(yaml.safe_load(path.read_text())).steps[-1].cleanup


def test_checkpoint_after_a_send_is_the_pages_response_not_a_nav_link() -> None:
    cap = build_capability(PAY, _meta(name="pay", success_text="Request Loan"))
    assert cap.checkpoint == "Bill Payment Complete"


def test_a_proof_inside_the_response_is_kept() -> None:
    proof = _ev(
        "finish_business_outcome", {"outcome": "paid", "proof_text": "Payment Complete"}, "OK"
    )
    assert build_capability([*PAY[:-3], proof], _meta(name="pay")).checkpoint == "Payment Complete"


def test_a_lone_logout_is_not_cleanup_and_is_refused_as_a_capability() -> None:
    log = [START, LOGOUT]
    (ev,) = step_events(log)
    assert ev["text"] == "Log Out"
    assert not ev.get("cleanup")
    with pytest.raises(ValueError, match="nothing was read or sent"):
        build_capability(log, _meta(name="bye"))


def test_a_login_only_run_is_refused() -> None:
    with pytest.raises(ValueError, match="nothing was read or sent"):
        build_capability(LOGIN, _meta())


def test_save_refuses_a_step_whose_label_is_a_typed_value() -> None:
    log = [*LOGIN, _ev("type_text", REF, "Typed.", label="Sean")]
    flag_leaks(log, {"sean"})
    with pytest.raises(ValueError, match="value typed this run") as err:
        build_capability(log, _meta(name="pay"))
    assert "sean" not in str(err.value).casefold()
    assert all(k != "value" for ev in log for k in ev)  # nothing but a flag stored


def test_flag_leaks_leaves_clean_events_alone() -> None:
    log = [*LOGIN, _ev("type_text", REF, "Typed.", label="Address:")]
    flag_leaks(log, {"sean"})
    assert not any(ev.get("leak") for ev in log)


def test_save_still_refuses_a_run_with_a_take_over_that_has_evidence() -> None:
    ev = _ev(
        "take_over",
        {"reason": "x"},
        "handed back",
        human_entry=True,
        recordable=False,
        actions=[{"kind": "page", "path": "/parabank/billpay.htm"}],
        shot_before=PNG,
        shot_after=PNG,
    )
    with pytest.raises(ValueError, match="take-over"):
        build_capability([*LOGIN, ev], _meta())


def test_input_name_slugs_a_label_and_never_starts_with_a_digit() -> None:
    assert input_name("Zip Code:") == "zip_code"
    assert input_name("74838") == "f_74838"
    assert input_name("::") == "value"


def test_a_dropdown_is_a_select_and_two_close_points_are_one_field() -> None:
    a = _ev("select_option", REF, "Selected.", label="From account #")
    b = {**a, "point": (330, 205)}
    assert is_select(a)
    assert is_select({**a, "tool": "request_value", "dropdown": True})
    assert same_spot(a, b)
    assert not same_spot(a, {**b, "point": (300, 260)})


class _Structured:
    def __init__(self, prompts: list[str]) -> None:
        self.prompts = prompts

    async def ainvoke(self, prompt: str) -> CapabilityMeta:
        self.prompts.append(prompt)
        return _meta(name="pay_bill")


class _FakeModel:
    """Stands in for a LangChain chat model: no network, records the prompt."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.schemas: list[type] = []

    def with_structured_output(self, schema: type) -> _Structured:
        self.schemas.append(schema)
        return _Structured(self.prompts)


@pytest.mark.asyncio
async def test_describe_asks_the_given_model_with_labels_and_input_names_only() -> None:
    model = _FakeModel()
    meta = await describe("Pay 4242 to Sean", PAY, model)
    assert meta.name == "pay_bill"
    assert model.schemas == [CapabilityMeta]
    (prompt,) = model.prompts
    assert "Inputs a caller fills in: amount." in prompt
    assert "type_text Amount" in prompt


def _logout() -> dict:
    return _ev("click", REF, "Clicked 'Log Out'.", "Request Loan", "Log Out", text="Log Out")


def _read() -> dict:
    args = {"save_as": "balance", "value_type": "currency", "description": "the balance"}
    return _ev("extract_value", args, "Saved.", label="Balance", table=None)


def test_a_second_login_never_moves_the_secrets_after_the_first_logout() -> None:
    """Live (get_account_transactions.yaml): log in, read, log out, log in again, log out. The
    'last success per field' rule kept the SECOND login's secrets, which landed after the first
    logout: replay clicked LOG IN on empty boxes and failed on the site's error page."""
    log = [*LOGIN, _read(), _logout(), *LOGIN[1:], _logout()]
    cap = build_capability(log, _meta(name="read_balance"))
    actions = [(s.action, getattr(s, "value", None)) for s in cap.steps]
    first_click = next(i for i, (a, _) in enumerate(actions) if a == "click")
    typed = [i for i, (_, v) in enumerate(actions) if v and "{{secret:" in v]
    assert typed
    assert all(i < first_click for i in typed)   # secrets come before the login click


def test_secrets_typed_after_the_login_click_are_refused() -> None:
    """A guard on the result: replay must never click Log In before the boxes are filled."""
    from cua.discovery.recorder import NotSaved  # noqa: PLC0415
    from cua.discovery.recorder.build import _check_login_order  # noqa: PLC0415
    steps = build_capability([*LOGIN, SENT], _meta()).steps
    _check_login_order(steps)                                   # in order: fine
    with pytest.raises(NotSaved, match="login"):
        _check_login_order([steps[2], steps[0], steps[1]])

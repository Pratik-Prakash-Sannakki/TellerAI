"""Tests for `cua.recorder`'s COMPILE half, ported from `notebooks/03_recorder.py`'s `OFFLINE`
cells. Every fixture's event shape and expected outcome is unchanged from the notebook -- these
call the real `cua.recorder`/`cua.schema` modules, not a re-implementation.

Zero API key, zero browser, zero network -- pure Python, hand-built fixture events throughout.
"""

from __future__ import annotations

import pathlib
import tempfile

import pytest
from pydantic import ValidationError

from cua.recorder import (
    ACCESSIBLE,
    CompileError,
    HUMAN_ENTRY_WHY,
    HUMAN_INPUT_PATTERN,
    classify_status,
    clean_events,
    compile_run,
    contains_literal,
    derive_target,
    drop_dead_end_risky_clicks,
    drop_detours,
    norm_url,
    rule_from_probe,
    same_value,
    save_capability,
    split_login,
    substitute,
    synthesize_human_entries,
    trim_tail,
    value_matches_type,
)
from cua.schema import from_yaml, to_yaml


# ---------- OFFLINE 2b: small helpers ----------
def test_norm_url():
    assert norm_url("https://parabank.parasoft.com/parabank/overview.htm") == "/overview.htm"
    assert norm_url("https://parabank.parasoft.com/parabank/activity.htm;jsessionid=ABC?id=13344") == "/activity.htm?id=13344"
    assert norm_url("https://evil.example/phish") == "https://evil.example/phish"


def test_contains_literal_word_boundary():
    assert contains_literal("id=13344", "13344")
    assert not contains_literal("$50", "5")
    assert not contains_literal("account_id", "id")


def test_substitute():
    assert substitute("/activity.htm?id=13344", {"account_id": "13344"}) == "/activity.htm?id={{account_id}}"


def test_same_value_numeric_canonicalization():
    assert same_value("$20.00", "20")
    assert same_value("20.00", "20.0")
    assert not same_value("013", "13")


def test_classify_status():
    assert classify_status("DENIED: 'register' is not allowed.") == "denied"
    assert classify_status("DECLINED earlier by a human. Do not retry.") == "declined"
    assert classify_status("BLOCKED: login already failed or hit its attempt limit.") == "blocked"
    assert classify_status("STOP: login failed (the login page reported: 'could not be verified').") == "stop"
    assert classify_status("SKIP: 'City' already has a value ('2').") == "skip"
    assert classify_status("NOT YET: you are still on the start page.") == "not_yet"
    assert classify_status("CLICK FAILED for [3]: TimeoutError") == "failed"
    assert classify_status("A human entered the value for 'Amount' themselves. ...") == "handoff"
    assert classify_status("A human took over and handed back. ...") == "handoff"
    assert classify_status("Clicked [3].") == "ok"
    assert classify_status("Typed into [1].") == "ok"


def test_value_matches_type():
    assert value_matches_type("$1,200.00", "currency")
    assert not value_matches_type("free", "currency")
    assert value_matches_type("42", "integer")
    assert not value_matches_type("x", "integer")


# ---------- OFFLINE 3b: locator derivation ----------
LOGIN_BUTTON_EL = {"role": "button", "name": "Log In", "name_source": "value", "label": None,
                    "text": None, "tag": "input", "type": "submit", "submit": True, "options": None,
                    "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
USERNAME_FIELD_EL = {"role": "textbox", "name": "Username", "name_source": "label", "label": "Username",
                      "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
PASSWORD_FIELD_EL = {"role": "textbox", "name": "Password", "name_source": "label", "label": "Password",
                      "text": None, "tag": "input", "type": "password", "submit": False, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 2, "name_count": 1, "label_count": 1}


def _expect_raises(fn, expect: str):
    with pytest.raises((CompileError, ValidationError, ValueError)) as exc_info:
        fn()
    assert expect in str(exc_info.value)


def test_derive_target_happy_path_role_unique():
    w = []
    t = derive_target(LOGIN_BUTTON_EL, {}, w)
    assert t.primary.strategy == "role" and t.primary.name == "Log In" and t.primary.within is None
    assert w == []


def test_derive_target_duplicate_name_scoped_via_within():
    edit_link = {"role": "link", "name": "Edit", "name_source": "text", "label": None, "text": "Edit",
                 "tag": "a", "type": None, "submit": False, "options": None,
                 "container": {"role": "table", "name": "Accounts"}, "nth": 2, "name_count": 2, "label_count": 1}
    w = []
    t = derive_target(edit_link, {}, w)
    assert t.primary.strategy == "role" and t.primary.within is not None
    assert t.primary.within.role == "table" and t.primary.within.name == "Accounts"
    assert w == []


def test_derive_target_duplicate_name_no_container_is_flagged_not_refused():
    edit_link_no_container = {"role": "link", "name": "Edit", "name_source": "text", "label": None,
                               "text": "Edit", "tag": "a", "type": None, "submit": False, "options": None,
                               "container": None, "nth": None, "name_count": 2, "label_count": 1}
    w = []
    t = derive_target(edit_link_no_container, {}, w)
    assert t.primary.within is None
    assert len(w) == 1 and "not unique" in w[0]


def test_derive_target_duplicate_label_is_refused_d68():
    dup_label_field = {"role": "textbox", "name": "", "name_source": "none", "label": "Amount",
                        "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                        "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 2}
    _expect_raises(lambda: derive_target(dup_label_field, {}, []), "no `within` scope for a 'label'")


def test_derive_target_attribute_only_name_is_not_a_role_locator():
    attr_only = {"role": "textbox", "name": "fromAccountId", "name_source": "attr", "label": "From account #:",
                 "text": None, "tag": "select", "type": None, "submit": False, "options": ["13344", "13355"],
                 "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
    t = derive_target(attr_only, {}, [])
    assert t.primary.strategy == "label"


def test_derive_target_data_dependent_name_has_no_structure_fallback():
    data_dep = {"role": "link", "name": "13344", "name_source": "text", "label": None, "text": "13344",
                "tag": "a", "type": None, "submit": False, "options": None,
                "container": {"role": "table", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
    t = derive_target(data_dep, {"account_id": "13344"}, [])
    assert t.primary.name == "{{account_id}}"
    assert t.fallback is None


def test_derive_target_nothing_to_identify_is_refused():
    _expect_raises(lambda: derive_target(
        {"role": "generic", "name": "", "name_source": "none", "label": None, "text": None,
         "tag": "div", "type": None, "submit": False, "options": None, "container": None, "nth": None,
         "name_count": 1, "label_count": 1}, {}, []), "no accessible name, label, text, or container")


# ---------- OFFLINE 4b: clean-up ----------
def _ev(i, tool, before, after, **kw):
    return {"i": i, "tool": tool, "args": kw.pop("args", {}), "status": kw.pop("status", "ok"),
            "before": {"url": before, "heading": kw.pop("before_heading", "")},
            "after": {"url": after, "heading": kw.pop("after_heading", "")}, **kw}


def test_clean_events_drops_non_actions_and_failures():
    events = [
        _ev(0, "observe", "/overview.htm", "/overview.htm"),
        _ev(1, "click", "/overview.htm", "/overview.htm", status="denied", el={"name": "register"}),
        _ev(2, "click", "/overview.htm", "/activity.htm?id=13344", el={"role": "link", "name": "13344", "name_source": "text"}),
    ]
    kept, dropped = clean_events(events)
    assert [e["i"] for e in kept] == [2]
    assert dropped == [(0, "observe", "not an action"), (1, "click", "did not work (denied)")]


def test_drop_detours_removes_a_click_away_click_back_pair():
    events = [
        _ev(0, "click", "/overview.htm", "/billpay.htm", el={"role": "link", "name": "Bill Pay", "name_source": "text"}),
        _ev(1, "click", "/billpay.htm", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"}),
        _ev(2, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"}),
    ]
    kept, dropped = clean_events(events)
    kept = drop_detours(kept, dropped)
    assert [e["i"] for e in kept] == [2]
    assert dropped[0][2].startswith("dead end:") and dropped[1][2].startswith("dead end:")


def test_trim_tail_drops_a_trailing_safe_link_click():
    events = [
        _ev(0, "extract_value", "/activity.htm?id=13344", "/activity.htm?id=13344", label="Balance:", save_as="balance", value_type="currency"),
        _ev(1, "click", "/activity.htm?id=13344", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"}),
    ]
    dropped = []
    task = trim_tail(list(events), dropped)
    assert [e["i"] for e in task] == [0]
    assert dropped == [(1, "click", "after the last meaningful step")]


def test_split_login():
    events = [
        _ev(0, "type_secret", "/index.htm", "/index.htm", value="username"),
        _ev(1, "type_secret", "/index.htm", "/index.htm", value="password"),
        _ev(2, "click", "/index.htm", "/overview.htm", el={"role": "button", "name": "Log In", "name_source": "value", "submit": True}),
        _ev(3, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"}),
    ]
    login_ev, task_ev = split_login(events)
    assert [e["i"] for e in login_ev] == [0, 1, 2]
    assert [e["i"] for e in task_ev] == [3]


# ---------- OFFLINE 4d: synthesize_human_entries ----------
PAYEE_NAME_EL = {"role": "textbox", "name": "payeeName", "name_source": "attr", "label": "Name",
                 "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                 "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 1,
                 "name_count": 1, "label_count": 1}
FROM_ACCOUNT_DROPDOWN_EL = {"role": "combobox", "name": "fromAccountId", "name_source": "attr",
                            "label": "Account", "text": None, "tag": "select", "type": None,
                            "submit": False, "options": ["12345", "67890"],
                            "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 1,
                            "name_count": 1, "label_count": 1}
CITY_FIELD_EL = {"role": "textbox", "name": "address.city", "name_source": "attr", "label": "City",
                 "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                 "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 2,
                 "name_count": 1, "label_count": 1}
TO_ACCOUNT_DROPDOWN_EL = {**FROM_ACCOUNT_DROPDOWN_EL, "name": "toAccountId", "options": ["AAA", "BBB"]}


def test_synthesize_one_text_field():
    out = synthesize_human_entries(5, "/billpay.htm", "Bill Payment Service", "/billpay.htm",
                                    "Bill Payment Service",
                                    [{"ref": 10, "el": PAYEE_NAME_EL, "value_after": "Nagarjuana"}])
    assert [e["i"] for e in out] == [5]
    assert out[0]["tool"] == "type_text" and out[0]["value"] == "Nagarjuana"
    assert out[0]["status"] == "ok" and out[0]["human_entered"] is True and out[0]["why"] == HUMAN_ENTRY_WHY
    assert out[0]["args"] == {"ref": 10, "text": "Nagarjuana"}


def test_synthesize_one_dropdown():
    out = synthesize_human_entries(5, "/billpay.htm", "Bill Payment Service", "/billpay.htm",
                                    "Bill Payment Service",
                                    [{"ref": 11, "el": FROM_ACCOUNT_DROPDOWN_EL, "value_after": "12345"}])
    assert out[0]["tool"] == "select_option" and out[0]["value"] == "12345"
    assert out[0]["args"] == {"ref": 11, "option": "12345"}


def test_synthesize_two_of_each_sequential_numbering():
    entries = [
        {"ref": 10, "el": PAYEE_NAME_EL, "value_after": "Nagarjuana"},
        {"ref": 12, "el": CITY_FIELD_EL, "value_after": "Springfield"},
        {"ref": 11, "el": FROM_ACCOUNT_DROPDOWN_EL, "value_after": "12345"},
        {"ref": 13, "el": TO_ACCOUNT_DROPDOWN_EL, "value_after": "BBB"},
    ]
    out = synthesize_human_entries(20, "/billpay.htm", "Bill Payment Service", "/billpay.htm",
                                    "Bill Payment Service", entries)
    assert [e["i"] for e in out] == [20, 21, 22, 23]
    assert [e["tool"] for e in out] == ["type_text", "type_text", "select_option", "select_option"]


def test_synthesize_skips_a_declined_field():
    entries_with_decline = [
        {"ref": 10, "el": PAYEE_NAME_EL, "value_after": "Nagarjuana"},
        {"ref": 12, "el": CITY_FIELD_EL, "value_after": ""},
        {"ref": 11, "el": FROM_ACCOUNT_DROPDOWN_EL, "value_after": "12345"},
    ]
    out = synthesize_human_entries(7, "/billpay.htm", "Bill Payment Service", "/billpay.htm",
                                    "Bill Payment Service", entries_with_decline)
    assert [e["i"] for e in out] == [7, 8]
    assert [e["tool"] for e in out] == ["type_text", "select_option"]
    assert {e["args"]["ref"] for e in out} == {10, 11}


# ---------- fixtures shared by the compile_run tests below ----------
def _e(i, tool, before, after, **kw):
    msg = kw.pop("message", None)
    status = kw.pop("status", classify_status(msg) if msg is not None else "ok")
    return {"i": i, "tool": tool, "args": kw.pop("args", {}),
            "before": {"url": before, "heading": kw.pop("before_heading", "")},
            "after": {"url": after, "heading": kw.pop("after_heading", "")},
            "message": msg or "", "status": status, **kw}


BAL_SPEC = {
    "name": "get_account_balance",
    "description": "Read the current balance of one account, given its account id.",
    "inputs": {"account_id": {"value": "13344", "type": "string", "description": "The account number.", "pattern": r"^[0-9]{4,10}$"}},
}


def _balance_events(extra_description: str | None = None) -> list[dict]:
    return [
        _e(0, "observe", "/index.htm", "/index.htm", before_heading="Customer Login", after_heading="Customer Login"),
        _e(1, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
        _e(2, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
        _e(3, "click", "/index.htm", "/overview.htm", el=LOGIN_BUTTON_EL, message="Clicked [3].",
           before_heading="Customer Login", after_heading="Accounts Overview"),
        _e(4, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"},
           message="Opened /activity.htm?id=13344.", before_heading="Accounts Overview", after_heading="Account Details"),
        _e(5, "extract_value", "/activity.htm?id=13344", "/activity.htm?id=13344",
           label="Balance:", save_as="balance", value_type="currency",
           description=extra_description or "Current balance, for example $1,200.00.",
           message="Read 'Balance:'.", before_heading="Account Details", after_heading="Account Details"),
        _e(6, "finish", "/activity.htm?id=13344", "/activity.htm?id=13344",
           summary="Read the balance.", values={"balance": "$1,200.00"}, message="Recorded. Stop now."),
    ]


def test_compile_run_good_balance_flow_login_split():
    result = compile_run(_balance_events(), BAL_SPEC)
    login, task, report = result["login"], result["task"], result["report"]
    assert login is not None and login.name == "login_parabank" and len(login.secrets) == 2
    assert [s.action for s in login.steps] == ["navigate", "type", "type", "click"]
    assert login.steps[0].path == "/index.htm"
    assert login.checkpoint.url_contains == "overview.htm" and login.checkpoint.text_present == "Accounts Overview"
    assert task.name == "get_account_balance" and task.secrets == []
    assert [s.action for s in task.steps] == ["navigate", "extract"]
    assert task.steps[0].path == "/activity.htm?id={{account_id}}"
    assert task.inputs[0].name == "account_id"
    assert task.outputs[0].name == "balance" and task.outputs[0].type == "currency"
    assert task.risk_level == "safe"
    assert any(r.kind == "recoverable" and r.action == "relogin" for r in task.outcome_rules)
    assert (0, "observe", "not an action") in report["dropped"]
    assert from_yaml(to_yaml(task)) == task and from_yaml(to_yaml(login)) == login


def test_compile_run_dead_end_click_is_removed():
    ev = _balance_events()
    detour = [
        _e(40, "click", "/overview.htm", "/billpay.htm", el={"role": "link", "name": "Bill Pay", "name_source": "text"}, message="Clicked [4]."),
        _e(41, "click", "/billpay.htm", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"}, message="Clicked [2]."),
    ]
    events = ev[:4] + detour + ev[4:]
    result2 = compile_run(events, BAL_SPEC)
    assert [s.action for s in result2["task"].steps] == ["navigate", "extract"]
    dead_ends = [d for d in result2["report"]["dropped"] if d[2].startswith("dead end:")]
    assert len(dead_ends) == 2 and {d[0] for d in dead_ends} == {40, 41}


def test_compile_run_output_description_is_parameterized():
    leaky_events = _balance_events(extra_description="Current balance of account 13344.")
    leaky_result = compile_run(leaky_events, {**BAL_SPEC})
    assert leaky_result["task"].outputs[0].description == "Current balance of account {{account_id}}."


XFER_SPEC = {
    "name": "transfer_funds",
    "description": "Move a stated amount from one account to another.",
    "inputs": {"amount": {"value": "20.00", "type": "currency", "description": "Amount to move.",
                          "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"}},
}
TRANSFER_BUTTON_EL = {"role": "button", "name": "Transfer", "name_source": "value", "label": None,
                      "text": None, "tag": "input", "type": "submit", "submit": True, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}


def test_compile_run_risky_click_produces_risk_risky():
    xfer_events = [
        _e(0, "click", "/transfer.htm", "/transfer.htm", el=TRANSFER_BUTTON_EL, approved=True,
           message="Clicked [5].", before_heading="Transfer Funds", after_heading="Transfer Complete!"),
        _e(1, "finish", "/transfer.htm", "/transfer.htm", summary="Transferred the amount.",
           values={"confirmation": "Transfer Complete!"}, message="Recorded. Stop now."),
    ]
    xfer_result = compile_run(xfer_events, XFER_SPEC)
    xfer_task = xfer_result["task"]
    click_step = xfer_task.steps[-1]
    assert click_step.action == "click" and click_step.risk == "risky" and click_step.amount_input == "amount"
    assert xfer_task.risk_level == "risky"
    assert xfer_task.checkpoint.url_contains == "transfer.htm" and xfer_task.checkpoint.text_present == "Transfer Complete!"


def test_rule_from_probe_business_outcome():
    probe_events = [
        _e(0, "open_path", "/overview.htm", "/activity.htm?id=00000", args={"path": "/activity.htm?id=00000"},
           message="Opened /activity.htm?id=00000."),
        _e(1, "finish_business_outcome", "/activity.htm?id=00000", "/activity.htm?id=00000",
           outcome="ACCOUNT_NOT_FOUND", proof="Could not find account 00000",
           message="Recorded as a business-outcome probe. Stop now."),
    ]
    rule = rule_from_probe(probe_events, {"account_id": "00000"})
    assert rule.kind == "business" and rule.outcome == "ACCOUNT_NOT_FOUND"
    assert rule.when.text_present == "Could not find account"


def test_compile_run_login_attempt_guard_refuses_entirely():
    guard_events = [
        _e(0, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
        _e(1, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
        _e(2, "click", "/index.htm", "/index.htm", el=LOGIN_BUTTON_EL,
           message="STOP: login failed (login was attempted 3 times with no success). Do not try again. Call finish with a summary starting 'STUCK:' explaining this."),
    ]
    assert guard_events[2]["status"] == "stop"
    with pytest.raises(CompileError, match="login attempt guard"):
        compile_run(guard_events, BAL_SPEC)


def test_compile_run_ask_human_handoff_refuses_the_whole_run():
    ask_human_events = [
        _e(0, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
        _e(1, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
        _e(2, "click", "/index.htm", "/overview.htm", el=LOGIN_BUTTON_EL, message="Clicked [3].",
           before_heading="Customer Login", after_heading="Accounts Overview"),
        _e(3, "ask_human", "/overview.htm", "/overview.htm",
           message="A human took over and handed back. Pages the human visited: none. Page now: .../overview.htm."),
    ]
    with pytest.raises(CompileError, match="no specific field known"):
        compile_run(ask_human_events, BAL_SPEC)


AMOUNT_FIELD_EL = {"role": "textbox", "name": "amount", "name_source": "attr", "label": "Amount",
                   "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                   "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 3,
                   "name_count": 1, "label_count": 1}
SEND_PAYMENT_BUTTON_EL = {"role": "button", "name": "Send Payment", "name_source": "value",
                          "label": None, "text": None, "tag": "input", "type": "submit",
                          "submit": True, "options": None,
                          "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 1,
                          "name_count": 1, "label_count": 1}
BILLPAY_SPEC = {
    "name": "pay_bill",
    "description": "Pay a bill to a named payee account from one source account.",
    "inputs": {
        "amount": {"value": "20.00", "type": "currency", "description": "Amount to pay.",
                   "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"},
        "payee_name": {"value": "Nagarjuana", "type": "string", "description": "Payee name as it appears on the bill-pay form.",
                       "pattern": r"^.{2,80}$"},
        "from_account": {"value": "12345", "type": "string", "description": "Account to pay from.",
                         "pattern": r"^[0-9]{4,10}$"},
    },
}


def _billpay_handoff_events():
    return [
        _e(0, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
        _e(1, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
        _e(2, "click", "/index.htm", "/overview.htm", el=LOGIN_BUTTON_EL, message="Clicked [3].",
           before_heading="Customer Login", after_heading="Accounts Overview"),
        _e(3, "click", "/overview.htm", "/billpay.htm", el={"role": "link", "name": "Bill Pay", "name_source": "text"},
           message="Clicked [4].", before_heading="Accounts Overview", after_heading="Bill Payment Service"),
        _e(4, "type_text", "/billpay.htm", "/billpay.htm", el=AMOUNT_FIELD_EL, value="20.00",
           message="Typed into [7].", before_heading="Bill Payment Service", after_heading="Bill Payment Service"),
        _e(5, "request_missing_values", "/billpay.htm", "/billpay.htm", args={"hints": {}},
           message="A human filled in what they chose to. Pages the human visited: none. Page now: .../billpay.htm.",
           before_heading="Bill Payment Service", after_heading="Bill Payment Service"),
        *synthesize_human_entries(6, "/billpay.htm", "Bill Payment Service", "/billpay.htm", "Bill Payment Service", [
            {"ref": 8, "el": PAYEE_NAME_EL, "value_after": "Nagarjuana"},
            {"ref": 9, "el": FROM_ACCOUNT_DROPDOWN_EL, "value_after": "12345"},
        ]),
        _e(8, "click", "/billpay.htm", "/billpay.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Bill Payment Complete!"),
        _e(9, "finish", "/billpay.htm", "/billpay.htm", summary="Paid the bill.",
           values={"confirmation": "Bill Payment Complete!"}, message="Recorded. Stop now."),
    ]


def test_compile_run_request_missing_values_handoff_compiles_with_synthetic_steps():
    result = compile_run(_billpay_handoff_events(), BILLPAY_SPEC)
    task = result["task"]
    synth_steps = [s for s in task.steps if s.why == HUMAN_ENTRY_WHY]
    assert len(synth_steps) == 2
    assert {s.action for s in synth_steps} == {"type", "select"}
    type_step = next(s for s in synth_steps if s.action == "type")
    select_step = next(s for s in synth_steps if s.action == "select")
    assert type_step.value == "{{payee_name}}"
    assert select_step.option == "{{from_account}}"
    assert {i.name for i in task.inputs} == {"amount", "payee_name", "from_account"}


REMARKS_FIELD_EL = {"role": "textbox", "name": "remarks", "name_source": "attr", "label": "Remarks",
                    "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                    "container": {"role": "form", "name": "Bill Payment Service"}, "nth": 5,
                    "name_count": 1, "label_count": 1}


def test_compile_run_unmatched_human_value_is_auto_declared_not_a_constant():
    events = [
        *_billpay_handoff_events()[:5],
        _e(5, "request_missing_values", "/billpay.htm", "/billpay.htm", args={"hints": {}},
           message="A human filled in what they chose to. Pages the human visited: none. Page now: .../billpay.htm.",
           before_heading="Bill Payment Service", after_heading="Bill Payment Service"),
        *synthesize_human_entries(6, "/billpay.htm", "Bill Payment Service", "/billpay.htm", "Bill Payment Service", [
            {"ref": 8, "el": PAYEE_NAME_EL, "value_after": "Nagarjuana"},
            {"ref": 9, "el": FROM_ACCOUNT_DROPDOWN_EL, "value_after": "12345"},
            {"ref": 14, "el": REMARKS_FIELD_EL, "value_after": "Thanks for your business"},
        ]),
        _e(9, "click", "/billpay.htm", "/billpay.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Bill Payment Complete!"),
        _e(10, "finish", "/billpay.htm", "/billpay.htm", summary="Paid the bill.",
           values={"confirmation": "Bill Payment Complete!"}, message="Recorded. Stop now."),
    ]
    spec = {**BILLPAY_SPEC, "inputs": dict(BILLPAY_SPEC["inputs"])}
    result = compile_run(events, spec)
    assert result["report"]["constants"] == []
    remarks_step = next(s for s in result["task"].steps
                         if s.action == "type" and s.why == HUMAN_ENTRY_WHY and s.value == "{{remarks}}")
    remarks_input = next(i for i in result["task"].inputs if i.name == "remarks")
    assert remarks_input.type == "string" and remarks_input.pattern == HUMAN_INPUT_PATTERN
    assert remarks_input.description == "Remarks, entered by a human during discovery -- provide the real value for each run."
    assert "amount" in {i.name for i in result["task"].inputs}
    # compile_run must never mutate the caller's own spec dict (D90)
    assert spec["inputs"].keys() == {"amount", "payee_name", "from_account"}


def test_compile_run_leftover_literal_still_refuses():
    leaky_spec = {**BILLPAY_SPEC, "inputs": dict(BILLPAY_SPEC["inputs"]),
                  "description": "Pay a bill to Nagarjuana from one source account."}
    with pytest.raises(CompileError) as exc_info:
        compile_run(_billpay_handoff_events(), leaky_spec)
    assert any("payee_name" in p and "description" in p for p in exc_info.value.problems)


def test_save_capability_happy_path_and_guards(tmp_path: pathlib.Path):
    result = compile_run(_balance_events(), BAL_SPEC)
    task = result["task"]
    path = save_capability(task, out_dir=tmp_path)
    assert path.name == "get_account_balance.yaml"
    assert from_yaml(path.read_text().split("\n", 1)[1]) == task

    # never write a stored secret value -- proven with a stand-in "forbidden" literal that is
    # known to appear in the YAML (the capability's own name), since a real captured account id
    # is already parameterized away by compile_run and would never appear literally either way
    with pytest.raises(CompileError, match="secret value"):
        save_capability(task, out_dir=tmp_path, forbidden=("get_account_balance",))

    # never overwrite a verified capability
    verified = task.model_copy(update={"status": "verified"})
    verified_path = tmp_path / "verified_cap.yaml"
    from cua.schema import to_yaml as _to_yaml

    verified2 = verified.model_copy(update={"name": "verified_cap"})
    verified_path.write_text(_to_yaml(verified2))
    with pytest.raises(CompileError, match="already verified"):
        save_capability(verified2, out_dir=tmp_path)


def test_drop_dead_end_risky_click_removed_when_proven_no_op():
    """OFFLINE 13d equivalent (D86): a risky click that changed nothing, retried later on the
    identical target, is a dead end and is removed."""
    events = [
        _e(0, "click", "/billpay.htm", "/billpay.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Bill Payment Service"),
        _e(1, "type_text", "/billpay.htm", "/billpay.htm", el=AMOUNT_FIELD_EL, value="20.00", message="Typed into [7]."),
        _e(2, "click", "/billpay.htm", "/billpay.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Bill Payment Complete!"),
    ]
    dropped = []
    kept, _ = clean_events(events)
    kept = drop_dead_end_risky_clicks(kept, dropped)
    assert [e["i"] for e in kept] == [1, 2]
    assert dropped[0][2].startswith("dead end: risky click had no effect")


def test_drop_dead_end_risky_click_never_touches_a_real_state_change():
    events = [
        _e(0, "click", "/billpay.htm", "/confirm.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Confirm Payment"),
        _e(1, "click", "/confirm.htm", "/confirm.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Confirm Payment", after_heading="Confirm Payment"),
    ]
    dropped = []
    kept, _ = clean_events(events)
    kept = drop_dead_end_risky_clicks(kept, dropped)
    assert [e["i"] for e in kept] == [0, 1]
    assert dropped == []


def test_drop_dead_end_risky_click_refuses_two_real_state_changes():
    events = [
        _e(0, "click", "/billpay.htm", "/step2.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Bill Payment Service", after_heading="Step 2"),
        _e(1, "click", "/step2.htm", "/step3.htm", el=SEND_PAYMENT_BUTTON_EL, approved=True,
           message="Clicked [10].", before_heading="Step 2", after_heading="Step 3"),
    ]
    dropped = []
    kept, _ = clean_events(events)
    with pytest.raises(CompileError, match="more than once in this run"):
        drop_dead_end_risky_clicks(kept, dropped)

"""Tests for `cua.schema`, ported from `notebooks/02_artifact_schema.py`'s offline check cells
(Sections 1b, 2b, 3b, 4b). Every assertion is unchanged in substance from the notebook -- these
now call the real `cua.schema` module instead of a namespace built by exec-ing the notebook.

Zero API key, zero browser, zero network.
"""

from __future__ import annotations

import copy
import pathlib

import pytest
import yaml
from pydantic import ValidationError

from cua.schema import (
    Capability,
    Checkpoint,
    Condition,
    Failure,
    LabelLocator,
    LabeledValueLocator,
    OutcomeRule,
    ReplayResult,
    RoleLocator,
    StructureLocator,
    Target,
    TextLocator,
    check_result,
    derived_routes,
    from_yaml,
    malformed_template,
    template_refs,
    to_yaml,
    tool_contract,
)

REPO = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "artifacts" / "examples"


def raises(fn, expect: str):
    with pytest.raises((ValidationError, ValueError)) as exc_info:
        fn()
    assert expect in str(exc_info.value)


# ---------- Section 1b: locators, conditions, steps, rules ----------
def test_target_primary_and_fallback_ok():
    Target(
        primary=RoleLocator(role="button", name="Log In", note="Accessible role+name; the most stable signal we have."),
        fallback=TextLocator(text="Log In", note="Visible text as a backup if the accessible name ever changes."),
    )


def test_target_rejects_fallback_more_stable_than_primary():
    raises(lambda: Target(
        primary=TextLocator(text="x", stability="low", note="n"),
        fallback=LabelLocator(label="x", stability="high", note="n"),
    ), "ordered from most to least stable")


def test_structure_locator_requires_within():
    raises(lambda: StructureLocator(tag="td", nth=18, note="n"), "within")


def test_locator_note_is_required():
    raises(lambda: RoleLocator(role="button", name="Log In"), "note")


def test_target_rejects_a_third_locator():
    raises(lambda: Target(
        primary=RoleLocator(role="button", name="Log In", note="n"),
        fallback=TextLocator(text="Log In", note="n"),
        third={"strategy": "text", "text": "x", "note": "n"},
    ), "Extra inputs are not permitted")


def test_condition_needs_one_signal():
    raises(lambda: Condition(), "needs url_contains or text_present")


def test_checkpoint_needs_both_signals():
    raises(lambda: Checkpoint(url_contains="activity.htm"), "needs both")


def test_business_rule_needs_outcome():
    raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="business", message="m"), "UPPER_SNAKE")


def test_hard_rule_carries_only_a_message():
    raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="hard", action="retry", message="m"),
           "hard rules carry only a message")


def test_labeled_value_only_allowed_in_extract():
    from cua.schema import Click

    raises(lambda: Click(target=Target(primary=LabeledValueLocator(label="Balance:", note="n"))),
           "only allowed in extract steps")


def test_navigate_path_must_start_with_slash():
    from cua.schema import Navigate

    raises(lambda: Navigate(path="overview.htm"), "String should match pattern")


def test_template_refs():
    assert template_refs("id={{account_id}} pw={{secret:password}}") == [(False, "account_id"), (True, "password")]


def test_malformed_template():
    assert malformed_template("{{Account}}")
    assert not malformed_template("{{account_id}}")


# ---------- Section 2b: Capability and YAML ----------
@pytest.fixture(scope="module")
def bal() -> Capability:
    return from_yaml((EXAMPLES / "get_account_balance.yaml").read_text())


@pytest.fixture(scope="module")
def xfer() -> Capability:
    return from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())


def test_examples_load(bal, xfer):
    assert bal.name == "get_account_balance"
    assert xfer.risk_level == "risky"


def test_derived_routes(bal, xfer):
    assert derived_routes(bal) == ["/activity.htm"]
    assert derived_routes(xfer) == ["/transfer.htm"]


def test_base_url_is_shape_checked():
    data = {**yaml.safe_load((EXAMPLES / "get_account_balance.yaml").read_text()), "base_url": "not-a-url"}
    raises(lambda: Capability.model_validate(data), "String should match pattern")


def _rejects(mutate, expect: str, source: str = "bal"):
    fname = "get_account_balance.yaml" if source == "bal" else "transfer_funds.yaml"
    data = copy.deepcopy(yaml.safe_load((EXAMPLES / fname).read_text()))
    mutate(data)
    raises(lambda: Capability.model_validate(data), expect)


def test_typo_in_a_key_is_rejected():
    _rejects(lambda d: d.update(descripton="x"), "Extra inputs are not permitted")


def test_unknown_input_reference_is_rejected():
    _rejects(lambda d: d["steps"][0].update(path="/activity.htm?id={{acount_id}}"), "unknown input 'acount_id'")


def test_malformed_template_in_path_is_rejected():
    _rejects(lambda d: d["steps"][0].update(path="/activity.htm?id={{Account}}"), "malformed template")


def test_output_never_extracted_is_rejected():
    _rejects(lambda d: d["steps"].pop(1), "must be produced by exactly one extract step")


def test_extract_into_undeclared_output_is_rejected():
    _rejects(lambda d: d["steps"][1].update(save_as="total"), "is not a declared output")


def test_duplicate_input_is_rejected():
    _rejects(lambda d: d["inputs"].append(copy.deepcopy(d["inputs"][0])), "duplicate input name")


def test_checkpoint_missing_text_is_rejected():
    _rejects(lambda d: d["checkpoint"].pop("text_present"), "a checkpoint needs both")


def test_business_rule_without_outcome_is_rejected():
    _rejects(lambda d: d["outcome_rules"][0].pop("outcome"), "business rules need an UPPER_SNAKE outcome")


def _bal_data_with_three_outcome_rules() -> dict:
    """`notebooks/02_artifact_schema.py`'s own Section 2b assumed `get_account_balance.yaml` had
    3 outcome_rules (index 1 recoverable, index 2 hard) -- true when that cell was written, but
    the example was later simplified to just the one business rule (D63-D66's rebuild), and the
    notebook's own check cell was never updated to match. Running the notebook today
    (`uv run python notebooks/02_artifact_schema.py`) reproduces this exactly: it crashes with
    `IndexError: list index out of range` at that very cell, before ever printing "ALL CHECKS
    PASSED" -- a genuine, pre-existing bug found during this port, not introduced by it (see the
    final report). This fixture restores a 3-rule shape by construction so the SAME two
    Capability-level validation rules are still tested end to end, rather than skipping them."""
    data = copy.deepcopy(yaml.safe_load((EXAMPLES / "get_account_balance.yaml").read_text()))
    data["outcome_rules"] = [
        data["outcome_rules"][0],   # the real business rule, unchanged
        {"when": {"text_present": "Customer Login"}, "kind": "recoverable", "action": "relogin", "message": "Session expired."},
        {"when": {"text_present": "Internal Error"}, "kind": "hard", "message": "Something broke."},
    ]
    return data


def test_recoverable_rule_without_action_is_rejected():
    data = _bal_data_with_three_outcome_rules()
    data["outcome_rules"][1].pop("action")
    raises(lambda: Capability.model_validate(data), "recoverable rules need an action")


def test_hard_rule_with_an_action_is_rejected():
    data = _bal_data_with_three_outcome_rules()
    data["outcome_rules"][2]["action"] = "retry"
    raises(lambda: Capability.model_validate(data), "hard rules carry only a message")


def test_bad_input_regex_is_rejected():
    _rejects(lambda d: d["inputs"][0].update(pattern="["), "pattern is not a valid regex")


def test_secret_used_as_plain_input_is_rejected():
    _rejects(lambda d: d["steps"][0].update(path="/activity.htm?id={{secret:password}}"), "only allowed as a typed value")


def test_labeled_value_in_a_click_is_rejected():
    def bad_click(d):
        d["steps"].insert(1, {"action": "click", "target": {"primary": {"strategy": "labeled_value", "label": "Balance:", "note": "n"}}})

    _rejects(bad_click, "only allowed in extract steps")


def test_locators_out_of_order_is_rejected():
    def bad_order(d):
        d["steps"][1]["target"] = {
            "primary": {"strategy": "text", "text": "Balance:", "stability": "low", "note": "n"},
            "fallback": {"strategy": "label", "label": "Balance:", "stability": "high", "note": "n"},
        }

    _rejects(bad_order, "ordered from most to least stable")


def test_page_wide_index_is_rejected():
    def page_wide_index(d):
        d["steps"][1]["target"] = {"primary": {"strategy": "structure", "tag": "td", "nth": 18, "note": "n"}}

    _rejects(page_wide_index, "within")


def test_locator_missing_note_is_rejected():
    def missing_note(d):
        d["steps"][1]["target"] = {"primary": {"strategy": "text", "text": "Balance:"}}

    _rejects(missing_note, "note")


def test_risky_step_but_risk_level_safe_is_rejected():
    _rejects(lambda d: d.update(risk_level="safe"), "risky but risk_level is 'safe'", "xfer")


def test_safe_capability_marked_risky_is_rejected():
    _rejects(lambda d: d.update(risk_level="risky"), "no step is marked risky")


def test_amount_input_not_declared_is_rejected():
    def bad_amount(d):
        d["steps"][4]["amount_input"] = "cash"

    _rejects(bad_amount, "is not a declared input", "xfer")


def test_yaml_round_trip_is_lossless(bal, xfer):
    for cap in (bal, xfer):
        assert from_yaml(to_yaml(cap)) == cap


# ---------- Section 3b: tool contract ----------
def test_tool_contract_required_inputs(xfer):
    contract = tool_contract(xfer)
    assert contract["input_schema"]["required"] == ["from_account", "to_account", "amount"]
    assert contract["returns"]["may_need_approval"] is True


def test_tool_contract_business_outcomes(bal):
    assert tool_contract(bal)["returns"]["business_outcomes"] == ["ACCOUNT_NOT_FOUND"]


def test_tool_contract_description_is_single_field(xfer):
    contract = tool_contract(xfer)
    assert contract["description"] == xfer.description
    assert "when_to_use" not in contract


# ---------- Section 4b: replay result contract ----------
def _ok(**kw):
    base = dict(run_id="r1", capability="get_account_balance", capability_version=1)
    return ReplayResult(**base, **kw)


def test_result_success(bal):
    check_result(bal, _ok(status="SUCCESS", outputs={"balance": "$1,200.00"}))


def test_result_business_outcome(bal):
    check_result(bal, _ok(status="BUSINESS_OUTCOME", outcome="ACCOUNT_NOT_FOUND"))


def test_result_needs_approval_shape():
    _ok(status="NEEDS_APPROVAL", pending_step=4, reason="amount above the auto-approve limit")


def test_result_failed_shape():
    _ok(status="FAILED", failure=Failure(step_index=1, step_action="extract",
                                          expected="a value next to 'Balance:'",
                                          observed="no such label on the page",
                                          evidence="evidence/r1/step1.png"))


def test_failed_without_failure_is_rejected():
    raises(lambda: _ok(status="FAILED"), "FAILED needs a failure")


def test_business_outcome_without_outcome_is_rejected():
    raises(lambda: _ok(status="BUSINESS_OUTCOME"), "needs an outcome")


def test_needs_approval_without_reason_is_rejected():
    raises(lambda: _ok(status="NEEDS_APPROVAL", pending_step=1), "needs pending_step and reason")


def test_success_with_an_outcome_is_rejected():
    raises(lambda: _ok(status="SUCCESS", outcome="X"), "SUCCESS carries only outputs")


def test_undeclared_outcome_is_rejected(bal):
    raises(lambda: check_result(bal, _ok(status="BUSINESS_OUTCOME", outcome="MADE_UP")), "is not declared")


def test_missing_output_is_rejected(bal):
    raises(lambda: check_result(bal, _ok(status="SUCCESS", outputs={})), "!= declared outputs")

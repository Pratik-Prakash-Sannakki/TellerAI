"""Tests for `cua.live`'s pure pieces: the pre-flight input gate (D91). Ported from
`notebooks/05_replay_live.py`'s own offline harness for `missing_required_inputs`/
`gather_missing_inputs` (`notebooks/scratch/test_preflight_gate.py`, referenced by DECISIONS.md
D91), run here via pytest against the real `cua.live` module instead of a scratch script.

`PlaywrightReplaySurface`/`make_escalate`/`replay_live` all need a real browser and are not
exercised here -- this file only covers the part of `cua.live` that is genuinely pure Python
(no page, no network), matching this port's own hard rule (zero browser in the test suite).
"""

from __future__ import annotations

import pathlib

import pytest

from cua.live import gather_missing_inputs, missing_required_inputs
from cua.replay import InputValidationError
from cua.schema import from_yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = REPO / "artifacts"


@pytest.fixture()
def pay_bill():
    return from_yaml((ARTIFACTS / "pay_bill.yaml").read_text())


@pytest.fixture()
def balance_cap():
    return from_yaml((ARTIFACTS / "get_account_balance.yaml").read_text())


def test_missing_required_inputs_finds_exactly_whats_missing(pay_bill):
    supplied = {"payee_name": "Nagarjuana", "amount": "20.00"}   # some supplied, some not, a gap in the middle
    missing = missing_required_inputs(pay_bill, supplied)
    missing_names = [p.name for p in missing]
    declared_order = [p.name for p in pay_bill.inputs if p.required]
    assert missing_names == [n for n in declared_order if n not in supplied]
    assert missing_names, "fixture capability should have at least one missing required input"


def test_missing_required_inputs_treats_whitespace_as_missing(pay_bill):
    supplied = {i.name: "x" for i in pay_bill.inputs}
    supplied[pay_bill.inputs[0].name] = "   "   # whitespace-only counts as missing (D91)
    missing = missing_required_inputs(pay_bill, supplied)
    assert missing and missing[0].name == pay_bill.inputs[0].name


def test_missing_required_inputs_empty_when_everything_supplied(pay_bill):
    supplied = {i.name: "x" for i in pay_bill.inputs}
    assert missing_required_inputs(pay_bill, supplied) == []


def test_missing_required_inputs_empty_capability_has_nothing_missing(balance_cap):
    assert balance_cap.inputs == []
    assert missing_required_inputs(balance_cap, {}) == []


def test_gather_missing_inputs_is_a_true_no_op_when_nothing_missing(pay_bill):
    supplied = {i.name: "x" for i in pay_bill.inputs}
    calls = []
    result = gather_missing_inputs(pay_bill, supplied, input_fn=lambda prompt: calls.append(prompt) or "should not be used")
    assert calls == []                       # input_fn never called even once
    assert result == supplied
    assert result is not supplied            # a new dict, caller's own dict never mutated


def _any_valid_answer(prompt: str) -> str:
    """A value that satisfies every one of pay_bill.yaml's declared input patterns -- 'amount'
    needs a currency shape, everything else just needs 1-80 non-empty characters."""
    return "20.00" if prompt.startswith("amount") else "sample-value-123"


def test_gather_missing_inputs_never_mutates_the_callers_dict(pay_bill):
    supplied = {}
    gather_missing_inputs(pay_bill, supplied, input_fn=_any_valid_answer)
    assert supplied == {}


def test_gather_missing_inputs_retries_an_empty_answer_then_accepts(pay_bill):
    """`pay_bill.yaml`'s human-entered inputs (D90) all carry the generic, permissive
    `^.{1,80}$` pattern, so any non-empty answer satisfies it -- the one real retry case a plain
    `input()` gate can exercise here is a blank first answer. Every OTHER required input is
    pre-supplied so exactly one field is ever prompted for."""
    target = next(p for p in pay_bill.inputs if p.required)
    supplied = {i.name: "x" for i in pay_bill.inputs if i.name != target.name}
    seq = iter(["", "a-valid-value"])   # blank (rejected, D91), then accepted
    result = gather_missing_inputs(pay_bill, supplied, input_fn=lambda prompt: next(seq))
    assert result[target.name] == "a-valid-value"


def test_gather_missing_inputs_gives_up_after_max_attempts(pay_bill):
    target = next(p for p in pay_bill.inputs if p.required)
    supplied = {i.name: "x" for i in pay_bill.inputs if i.name != target.name}
    with pytest.raises(InputValidationError, match=target.name):
        gather_missing_inputs(pay_bill, supplied, input_fn=lambda prompt: "", max_attempts=2)

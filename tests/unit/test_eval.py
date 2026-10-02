"""cua.eval: summarize N replay results into a stability report. Pure, no browser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import JsonValue

from cua import eval as ev
from cua.schema import Capability, ReplayResult

SECRET_OUT = "4242.17"  # an output value: must never reach the report or report.json


def _row(step: int, rung: str, **kw: JsonValue) -> dict[str, JsonValue]:
    return {"step": step, "action": "click", "rung": rung, **kw}


def _ok(rung_step1: str, value: str = SECRET_OUT) -> ReplayResult:
    drift = [_row(0, "rung1"), _row(1, rung_step1), _row(2, "rung1", cleanup=True)]
    return ReplayResult("SUCCESS", {"balance": value}, drift, cleanup="done")


def _three() -> list[ReplayResult]:
    failed = ReplayResult(
        "FAILED", {}, [_row(0, "table"), _row(1, "human")], "target not found",
        human=[{"step": 1}],
    )  # fmt: skip
    return [_ok("rung1"), _ok("rung3"), failed]


def test_counts_rate_and_assisted() -> None:
    r = ev.summarize(_three())
    assert (r.runs, r.status_counts) == (3, {"SUCCESS": 2, "FAILED": 1})
    assert r.success_rate == pytest.approx(2 / 3)
    assert r.assisted == 1
    assert r.flaky is True
    assert r.all_success is False


def test_the_rung_histogram_keeps_cleanup_rows_apart() -> None:
    r = ev.summarize(_three())
    assert r.rungs == {0: {"rung1": 2, "table": 1}, 1: {"rung1": 1, "rung3": 1, "human": 1}}
    assert r.cleanup_rungs == {2: {"rung1": 2}}


def test_a_step_that_left_its_first_choice_rung_is_a_fallback() -> None:
    results = [_ok("rung1"), _ok("rung1"), _ok("rung3")]
    assert ev.summarize(results).fallback_steps == [1]
    assert ev.summarize([_ok("rung1"), _ok("table")]).fallback_steps == []


def test_steps_without_a_target_and_relogins_are_not_fallbacks() -> None:
    drift = [_row(0, "-"), _row(1, "recover"), _row(1, "rung1+anchor"), _row(2, "skipped")]
    r = ev.summarize([ReplayResult("SUCCESS", {}, drift)])
    assert r.fallback_steps == []


def test_same_statuses_are_not_flaky() -> None:
    r = ev.summarize([_ok("rung1"), _ok("rung1")])
    assert (r.flaky, r.all_success, r.success_rate) == (False, True, 1.0)


def test_outputs_stable_when_every_success_returns_the_same_values() -> None:
    r = ev.summarize([_ok("rung1"), _ok("rung1"), _three()[2]])  # a failure is ignored
    assert (r.outputs_stable, r.output_stable) == (True, {"balance": True})


def test_outputs_unstable_when_a_value_or_a_key_differs() -> None:
    r = ev.summarize([_ok("rung1"), _ok("rung1", "1.00")])
    assert (r.outputs_stable, r.output_stable) == (False, {"balance": False})
    extra = ReplayResult("SUCCESS", {"balance": SECRET_OUT, "other": "x"}, [])
    r = ev.summarize([_ok("rung1"), extra])
    assert r.output_stable == {"balance": True, "other": False}
    assert r.outputs_stable is False


def test_no_success_run_is_not_stable() -> None:
    assert ev.summarize([_three()[2]]).outputs_stable is False


def test_render_is_a_short_table_without_values() -> None:
    text = ev.render(ev.summarize(_three()))
    for part in ("runs: 3", "SUCCESS 2", "FAILED 1", "flaky: yes", "<- fallback"):
        assert part in text
    assert SECRET_OUT not in text


def test_report_json_has_no_output_value_and_masks_reasons(tmp_path: Path) -> None:
    report = ev.summarize(_three())
    rows = ev.run_rows(_three(), [{SECRET_OUT}, set(), {"target"}])
    folder = ev.save_report(report, rows, "cap_name", tmp_path, {"git_sha": "abc"})
    assert folder.parent == tmp_path
    assert folder.name.endswith("-cap_name")
    text = (folder / "report.json").read_text()
    assert SECRET_OUT not in text
    data = json.loads(text)
    assert data["report"]["status_counts"] == {"SUCCESS": 2, "FAILED": 1}
    assert data["runs"][2] == {"run": 3, "status": "FAILED", "reason": "*** not found"}
    assert json.loads((folder / "run.json").read_text()) == {"git_sha": "abc"}


def _cap(steps: list[dict[str, object]], inputs: list[str]) -> Capability:
    return Capability.model_validate(
        {
            "name": "c", "description": "d", "base_url": "https://h", "viewport": [1, 1],
            "inputs": [{"name": n} for n in inputs], "steps": steps, "checkpoint": "ok",
        }
    )  # fmt: skip


T = {"anchor": {"label": "L", "offset": [0, 0]}}
LOGIN = [
    {"action": "type", "target": T, "value": "{{secret:username}}"},
    {"action": "click", "target": T},
]


def test_missing_inputs_by_name_any_case() -> None:
    cap = _cap([*LOGIN, {"action": "type", "target": T, "value": "{{amount}}"}], ["amount", "to"])
    assert ev.missing_inputs(cap, {"AMOUNT": "1"}) == ["to"]
    assert ev.missing_inputs(cap, {"amount": "1", "to": "2"}) == []
    assert ev.missing_inputs(cap, {"amount": ""}) == ["amount", "to"]


def test_a_click_after_typing_an_input_sends_data() -> None:
    form = {"action": "type", "target": T, "value": "{{amount}}"}
    assert ev.sends_data(_cap([*LOGIN, form, {"action": "click", "target": T}], ["amount"]))
    assert not ev.sends_data(_cap(LOGIN, []))  # the login alone is not a send
    logout = {"action": "click", "target": T, "cleanup": True}
    assert not ev.sends_data(_cap([*LOGIN, form, logout], ["amount"]))

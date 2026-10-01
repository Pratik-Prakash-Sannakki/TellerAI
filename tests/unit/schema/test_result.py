"""ReplayResult summary/outputs_line, Stop, and the Status values."""

from __future__ import annotations

from cua.schema import ReplayResult, Status, Stop


def test_status_values_are_the_plain_strings() -> None:
    assert [s.value for s in Status] == [
        "SUCCESS",
        "BUSINESS_OUTCOME",
        "DECLINED",
        "STUCK",
        "FAILED",
    ]
    assert Status.SUCCESS == "SUCCESS"


def test_success_outputs_line() -> None:
    r = ReplayResult(status=Status.SUCCESS, outputs={"a": "1"}, drift=[])
    assert r.outputs_line == "outputs: {'a': '1'}"
    assert r.summary == "SUCCESS"


def test_partial_outputs_line_when_not_success() -> None:
    r = ReplayResult(status="STUCK", outputs={}, drift=[])
    assert r.outputs_line == "partial outputs (run did not succeed): {}"


def test_summary_names_the_human_steps() -> None:
    one = ReplayResult(status="SUCCESS", outputs={}, drift=[], human=[{"step": 0}])
    two = ReplayResult(status="SUCCESS", outputs={}, drift=[], human=[{"step": 1}, {"step": 3}])
    assert one.summary == "SUCCESS (human intervened at step 1)"
    assert two.summary == "SUCCESS (human intervened at steps 2, 4)"


def test_result_defaults() -> None:
    r = ReplayResult(status="FAILED", outputs={}, drift=[])
    assert (r.reason, r.human, r.failure, r.recoveries, r.cleanup) == ("", [], None, 0, "")


def test_stop_carries_its_fields() -> None:
    e = Stop("STUCK", "no match", expected="email", observed="x")
    assert (e.status, e.reason, e.expected, e.observed, str(e)) == (
        "STUCK",
        "no match",
        "email",
        "x",
        "no match",
    )

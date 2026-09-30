"""save_evidence writes one masked folder per run: summary, drift, failure (only when not SUCCESS), final, capability."""
import json

import cv2
import numpy as np
import pytest
import yaml

from test_load_inputs import CAP, _write

VALUE, SECRET = "Sean Park", "p-secret"


def _png(ns, text: str) -> bytes:
    img = np.full((60, 300, 3), 255, np.uint8)
    cv2.putText(img, text, (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return ns["encode"](img)


@pytest.fixture
def run(ns, tmp_path):
    """A capability on disk, a fake OCR that reads the value, and the last run's in-memory mask set."""
    cap_path = _write(tmp_path, CAP)
    ns["ocr"] = lambda img: [(f"Payee {VALUE}", ns["Box"](0, 0, 200, 50)), ("Pay", ns["Box"](210, 0, 250, 50))]
    ns["LAST_RUN"].update(values={VALUE, "74838"}, final=_png(ns, VALUE))
    return ns, cap_path, tmp_path / "out"


def _result(ns, status, failure=None):
    shots = {"start": b"", "end": None}
    drift = [{"step": 0, "action": "type", "rung": "rung2", "point": (10, 20), "attempt": 1, "checked": True},
             {"step": 1, "action": "click", "rung": "human", "shots": shots,
              "actions": {"pages": ["/parabank/billpay.htm"], "sends": []}}]
    drift[1]["shots"]["start"] = ns["LAST_RUN"]["final"]
    human = [{"step": 1, "reason": f"box shows {VALUE}", "actions": drift[1]["actions"]}]
    return ns["ReplayResult"](status, {"balance": "74838"}, drift, f"typed {VALUE} and {SECRET}", human,
                              failure)


def _all_text(folder) -> str:
    return "".join(p.read_bytes().decode("latin-1") for p in folder.iterdir())


def test_all_files_are_written(run) -> None:
    ns, cap_path, out = run
    fail = {"step": 1, "action": "click", "expected": "Transfer Complete!", "observed": f"Hi {VALUE}"}
    folder = ns["save_evidence"](_result(ns, "FAILED", fail), cap_path, out)
    assert folder.parent == out and folder.name.endswith("-get_balance")
    assert sorted(p.name for p in folder.iterdir()) == [
        "capability.yaml", "drift.jsonl", "failure.json", "final.png", "summary.json", "take_over_0_before.png"]
    assert yaml.safe_load((folder / "capability.yaml").read_text())["name"] == "get_balance"
    lines = [json.loads(x) for x in (folder / "drift.jsonl").read_text().splitlines()]
    assert lines[0] == {"step": 0, "action": "type", "rung": "rung2", "point": [10, 20], "attempt": 1, "checked": True}
    assert lines[1]["shots"] == {"before": "take_over_0_before.png", "after": None}
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["status"] == "FAILED" and summary["summary"] == "FAILED (human intervened at step 2)"
    assert summary["failing_step"] == 1 and summary["outputs"] == {"balance": "***"}


def test_no_input_value_or_secret_in_any_file(run) -> None:
    ns, cap_path, out = run
    fail = {"step": 1, "action": "click", "expected": "Transfer Complete!", "observed": f"Hi {VALUE} {SECRET}"}
    folder = ns["save_evidence"](_result(ns, "FAILED", fail), cap_path, out)
    text = _all_text(folder)
    for leak in (VALUE, "74838", SECRET, "u-secret"):
        assert leak not in text
    final = cv2.imdecode(np.frombuffer((folder / "final.png").read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    assert final[:50, :200].max() == 0                     # the box reading the value is blacked out


def test_failure_json_has_step_expected_observed(run) -> None:
    ns, cap_path, out = run
    fail = {"step": 3, "action": "checkpoint", "expected": "Transfer Complete!", "observed": f"Error for {VALUE}"}
    folder = ns["save_evidence"](_result(ns, "FAILED", fail), cap_path, out)
    assert json.loads((folder / "failure.json").read_text()) == {
        "step": 3, "action": "checkpoint", "expected": "Transfer Complete!", "observed": "Error for ***"}


def test_no_failure_file_on_success(run) -> None:
    ns, cap_path, out = run
    ns["LAST_RUN"]["final"] = None
    folder = ns["save_evidence"](_result(ns, "SUCCESS"), cap_path, out)
    assert not (folder / "failure.json").exists() and not (folder / "final.png").exists()
    assert json.loads((folder / "summary.json").read_text())["failing_step"] is None


def test_checkpoint_miss_carries_expected_and_observed(ns, mk_look) -> None:
    import asyncio
    lk = mk_look([("Error", (0, 0, 40, 10)), ("x" * 300, (0, 20, 40, 30))])

    async def take_look():
        ns["STATE"].look = lk
        return lk

    ns.update(take_look=take_look, CFG=ns["Config"](check_s=0))
    ns["STATE"].look = lk
    cap = ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                           viewport=(1280, 800), checkpoint="Transfer Complete!",
                           steps=[ns["SCHEMA"]["Navigate"](path="/x")])

    async def nav(step, point, cap):
        return True

    ns["ACTIONS"] = {**ns["ACTIONS"], "navigate": nav}
    with pytest.raises(ns["Stop"]) as e:
        asyncio.run(ns["walk"](cap, None, []))
    assert e.value.expected == "Transfer Complete!" and e.value.observed == lk.text[:200]
    assert ns["STATE"].step == 1 and ns["STATE"].action == "checkpoint"      # after the last step

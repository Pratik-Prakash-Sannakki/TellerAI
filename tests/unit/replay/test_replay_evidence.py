"""save_evidence writes one masked folder per run: summary, drift, failure (only when not
SUCCESS), final, capability, run.json. Ported from tests/replay/test_replay_evidence.py and the
evidence tests of test_table_replay.py."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
import yaml

from cua.replay.context import Ctx
from cua.replay.evidence import masked_outputs, save_evidence
from cua.safety.redact import REPLAY_NUMBER, redactor
from cua.schema import ReplayResult
from cua.vision import Box, encode
from tests.unit.replay.helpers import make_replay_ctx, write_cap
from tests.unit.replay.test_replay_table import COLS, WANT

VALUE, SECRET = "Sean Park", "p-secret"


def _png(text: str) -> bytes:
    img = np.full((60, 300, 3), 255, np.uint8)
    cv2.putText(img, text, (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return encode(img)


def fake_ocr(img: object) -> list[tuple[str, Box]]:
    return [(f"Payee {VALUE}", Box(0, 0, 200, 50)), ("Pay", Box(210, 0, 250, 50))]


@pytest.fixture
def run(tmp_path: Path) -> tuple[Ctx, Path, Path]:
    """A capability on disk, a fake OCR that reads the value, and the last run's mask set."""
    ctx = make_replay_ctx()
    ctx.last.values, ctx.last.final = {VALUE, "74838"}, _png(VALUE)
    return ctx, write_cap(tmp_path), tmp_path / "out"


def _result(ctx: Ctx, status: str, failure: dict[str, object] | None = None) -> ReplayResult:
    shots = {"start": ctx.last.final, "end": None}
    actions = {"pages": ["/parabank/billpay.htm"], "sends": []}
    drift = [
        {
            "step": 0,
            "action": "type",
            "rung": "rung2",
            "point": (10, 20),
            "attempt": 1,
            "checked": True,
        },
        {"step": 1, "action": "click", "rung": "human", "shots": shots, "actions": actions},
    ]
    human = [{"step": 1, "reason": f"box shows {VALUE}", "actions": actions}]
    return ReplayResult(status, {"balance": "74838"}, drift, f"typed {VALUE} and {SECRET}", human, failure)  # type: ignore[arg-type]


def _save(ctx: Ctx, res: ReplayResult, cap_path: Path, out: Path) -> Path:
    return save_evidence(ctx, res, cap_path, out, fake_ocr)  # type: ignore[arg-type]


def _all_text(folder: Path) -> str:
    return "".join(p.read_bytes().decode("latin-1") for p in folder.iterdir())


def test_all_files_are_written(run: tuple[Ctx, Path, Path]) -> None:
    ctx, cap_path, out = run
    fail = {
        "step": 1,
        "action": "click",
        "expected": "Transfer Complete!",
        "observed": f"Hi {VALUE}",
    }
    folder = _save(ctx, _result(ctx, "FAILED", fail), cap_path, out)
    assert folder.parent == out and folder.name.endswith("-get_balance")
    assert sorted(p.name for p in folder.iterdir()) == [
        "capability.yaml",
        "drift.jsonl",
        "failure.json",
        "final.png",
        "run.json",
        "summary.json",
        "take_over_0_before.png",
    ]
    assert yaml.safe_load((folder / "capability.yaml").read_text())["name"] == "get_balance"
    lines = [json.loads(x) for x in (folder / "drift.jsonl").read_text().splitlines()]
    assert lines[0] == {
        "step": 0,
        "action": "type",
        "rung": "rung2",
        "point": [10, 20],
        "attempt": 1,
        "checked": True,
    }
    assert lines[1]["shots"] == {"before": "take_over_0_before.png", "after": None}
    summary = json.loads((folder / "summary.json").read_text())
    assert (
        summary["status"] == "FAILED"
        and summary["summary"] == "FAILED (human intervened at step 2)"
    )
    assert summary["failing_step"] == 1 and summary["outputs"] == {"balance": "***"}


def test_run_json_has_provenance_and_no_values(run: tuple[Ctx, Path, Path]) -> None:
    ctx, cap_path, out = run
    folder = _save(ctx, _result(ctx, "SUCCESS"), cap_path, out)
    info = json.loads((folder / "run.json").read_text())
    assert set(info) == {"prompt_version", "model", "config_hash", "git_sha"}
    assert info["prompt_version"] is None and info["model"] is None
    assert len(info["config_hash"]) == 64 and info["git_sha"]


def test_no_input_value_or_secret_in_any_file(run: tuple[Ctx, Path, Path]) -> None:
    ctx, cap_path, out = run
    fail = {
        "step": 1,
        "action": "click",
        "expected": "Transfer Complete!",
        "observed": f"Hi {VALUE} {SECRET}",
    }
    folder = _save(ctx, _result(ctx, "FAILED", fail), cap_path, out)
    text = _all_text(folder)
    for leak in (VALUE, "74838", SECRET, "u-secret"):
        assert leak not in text
    final = cv2.imdecode(
        np.frombuffer((folder / "final.png").read_bytes(), np.uint8), cv2.IMREAD_COLOR
    )
    assert final[:50, :200].max() == 0  # the box reading the value is blacked out


def test_failure_json_has_step_expected_observed(run: tuple[Ctx, Path, Path]) -> None:
    ctx, cap_path, out = run
    fail = {
        "step": 3,
        "action": "checkpoint",
        "expected": "Transfer Complete!",
        "observed": f"Error for {VALUE}",
    }
    folder = _save(ctx, _result(ctx, "FAILED", fail), cap_path, out)
    assert json.loads((folder / "failure.json").read_text()) == {
        "step": 3,
        "action": "checkpoint",
        "expected": "Transfer Complete!",
        "observed": "Error for ***",
    }


def test_no_failure_file_on_success(run: tuple[Ctx, Path, Path]) -> None:
    ctx, cap_path, out = run
    ctx.last.final = None
    folder = _save(ctx, _result(ctx, "SUCCESS"), cap_path, out)
    assert not (folder / "failure.json").exists() and not (folder / "final.png").exists()
    assert json.loads((folder / "summary.json").read_text())["failing_step"] is None


def test_a_short_number_is_masked_only_as_a_whole_number() -> None:
    redact = redactor({"1", "15231"}, number=REPLAY_NUMBER)
    assert redact("rung1 attempt 1 #15231 $1.00 s1.png") == "rung1 attempt *** #*** *** s1.png"


def test_evidence_masks_every_cell(tmp_path: Path) -> None:
    ctx = make_replay_ctx()
    res = ReplayResult("SUCCESS", {"transactions_1": WANT, "balance": "$5.00"}, [])  # type: ignore[dict-item]
    folder = _save(ctx, res, write_cap(tmp_path), tmp_path / "out")
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["outputs"] == {
        "transactions_1": [dict.fromkeys(COLS, "***")] * 2,
        "balance": "***",
    }
    assert "Bill Payment" not in (folder / "summary.json").read_text()


@pytest.mark.parametrize("rows", [[], WANT])
def test_masked_outputs_keep_the_shape(rows: list[dict[str, str]]) -> None:
    assert masked_outputs({"t": rows}) == {"t": [dict.fromkeys(r, "***") for r in rows]}

"""save_evidence: one masked folder per run. No run value or secret is ever written in clear.
Ported from tests/discovery/test_evidence.py (redactor and mask_png are tested in
tests/unit/safety); plus run.json (Decision 5)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from cua import evidence as shared
from cua.discovery.agent.prompt import PROMPT_VERSION
from cua.discovery.evidence import save_evidence, transcript
from cua.discovery.run import DiscoveryRun
from tests.fakes import make_ctx

SECRET, ACCOUNT, NAME = "hunter2-pw", "14454", "Sean"
SEND = "/app/services/bank/billpay"
LOG = [
    {
        "tool": "start",
        "args": {"base_url": "https://example.test/app"},
        "result": "run started",
        "point": None,
        "url": "https://example.test/app/",
        "crop": None,
    },
    {
        "tool": "type_secret",
        "args": {"secret_name": "password"},
        "result": "Typed secret 'password'.",
        "point": [300, 200],
        "url": "https://example.test/app/index.htm",
        "crop": b"c1",
    },
    {
        "tool": "take_over",
        "args": {"reason": "user asked"},
        "result": "handed back",
        "point": None,
        "url": "https://example.test/app/overview.htm",
        "crop": None,
        "recordable": False,
        "actions": [{"kind": "page", "path": "/app/billpay.htm"}, {"kind": "send", "path": SEND}],
        "shot_before": b"s0",
        "shot_after": b"s1",
    },
    {
        "tool": "send",
        "args": {"path": SEND},
        "result": "approved by human",
        "point": None,
        "url": f"https://example.test/app/billpay.htm?payee={NAME}",
        "crop": None,
    },
]
MESSAGES = [
    SimpleNamespace(type="human", content=f"Log in, pay {NAME} $100000", tool_calls=[]),
    SimpleNamespace(
        type="ai",
        content=[{"type": "text", "text": f"Paying {NAME} from {ACCOUNT}."}],
        tool_calls=[{"name": "click", "args": {}}, {"name": "type_text", "args": {}}],
    ),
    SimpleNamespace(type="tool", content=[{"type": "image", "data": "..."}], tool_calls=[]),
    SimpleNamespace(type="ai", content="Done. Bill Payment Complete.", tool_calls=[]),
]
SHA256_HEX = 64
ANSWER = f"Done. {NAME} was paid $100,000.00 from account {ACCOUNT}. Bill Payment Complete."


@pytest.fixture
def masked(monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
    """The OCR mask is tested in tests/unit/safety; here: that every PNG goes through it."""
    seen: list[bytes] = []

    def mask(png: bytes, redact: object, ocr_fn: object) -> bytes:
        seen.append(png)
        return b"MASKED:" + png

    monkeypatch.setattr(shared, "mask_png", mask)
    return seen


def _save(
    tmp_path: Path, answer: str = ANSWER, shot: bytes | None = None, capability: Path | None = None
) -> Path:
    ctx = make_ctx(secrets={"username": "jdoe", "password": SECRET})
    run = DiscoveryRun(
        goal=f"Log in, pay {NAME} $100000",
        answer=answer,
        log=[dict(e) for e in LOG],  # type: ignore[misc]
        redact={"100000", ACCOUNT, NAME, "jdoe"},
        messages=list(MESSAGES),
        final_shot=shot,
    )
    ctx.guard.state = run
    return save_evidence(ctx, tmp_path / "ev", capability, model="claude-x", ocr_fn=lambda i: [])


def test_writes_one_folder_with_every_file(tmp_path: Path, masked: list[bytes]) -> None:
    run = _save(tmp_path)
    assert run.parent == tmp_path / "ev"
    assert re.fullmatch(r"\d{8}T\d{6}Z-log_in_pay", run.name), run.name
    names = {p.name for p in run.iterdir()}
    assert {
        "goal.txt",
        "events.jsonl",
        "answer.txt",
        "summary.json",
        "run.json",
        "step_1.png",
        "take_over_0_before.png",
        "take_over_0_after.png",
    } <= names
    assert sorted(masked) == [b"c1", b"s0", b"s1"]
    events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
    assert len(events) == len(LOG)
    assert events[1]["crop"] == "step_1.png"
    assert events[2]["shot_before"] == "take_over_0_before.png"
    summary = json.loads((run / "summary.json").read_text())
    assert summary["events"] == len(LOG)
    assert summary["take_over"] is True
    assert summary["capability_saved"] is None
    assert summary["take_overs"][0]["actions"][1] == {"kind": "send", "path": SEND}


def test_no_value_is_ever_written_in_clear(tmp_path: Path, masked: list[bytes]) -> None:
    run = _save(tmp_path)
    assert "sean" not in run.name
    assert "100000" not in run.name
    for f in run.iterdir():
        text = f.read_bytes().decode("latin-1")
        for value in (SECRET, ACCOUNT, NAME, "100000", "100,000", "jdoe"):
            assert value.casefold() not in text.casefold(), f"{value} leaked in {f.name}"
    assert "Bill Payment Complete" in (run / "answer.txt").read_text()
    assert "paid *** from account ***" in (run / "answer.txt").read_text()


def test_a_failed_run_still_writes_evidence(tmp_path: Path, masked: list[bytes]) -> None:
    run = _save(tmp_path, answer="STUCK: the page did not load")
    assert json.loads((run / "summary.json").read_text())["status"] == "STUCK"


def test_transcript_keeps_ai_text_and_tool_names_masked(
    tmp_path: Path, masked: list[bytes]
) -> None:
    run = _save(tmp_path)
    rows = [json.loads(line) for line in (run / "transcript.jsonl").read_text().splitlines()]
    assert rows == [
        {"i": 0, "text": "Paying *** from ***.", "tools": ["click", "type_text"]},
        {"i": 1, "text": "Done. Bill Payment Complete.", "tools": []},
    ]
    assert transcript([], str) == []


def test_final_shot_is_written_masked_for_a_stuck_run_only(
    tmp_path: Path, masked: list[bytes]
) -> None:
    run = _save(tmp_path, answer="STUCK: no page", shot=b"end")
    assert (run / "final.png").read_bytes() == b"MASKED:end"
    assert b"end" in masked
    run = _save(tmp_path / "ok")
    assert not (run / "final.png").exists()


def _artifact(tmp_path: Path, text: str) -> Path:
    art = tmp_path / "art"
    (art / "crops/pay").mkdir(parents=True)
    (art / "crops/pay/s0.png").write_bytes(b"crop")
    (art / "pay.yaml").write_text(text)
    return art / "pay.yaml"


def test_capability_yaml_and_crops_are_copied(tmp_path: Path, masked: list[bytes]) -> None:
    yml = _artifact(tmp_path, "name: pay\ninputs: {payee: string}\n")
    run = _save(tmp_path, capability=yml)
    assert (run / "capability.yaml").read_text() == yml.read_text()
    assert (run / "crops/pay/s0.png").read_bytes() == b"crop"


def test_an_artifact_holding_a_run_value_is_refused(tmp_path: Path, masked: list[bytes]) -> None:
    yml = _artifact(tmp_path, f"name: pay\npayee: {NAME}\n")
    with pytest.raises(ValueError, match="a run value is in the artifact"):
        _save(tmp_path, capability=yml)
    assert not list((tmp_path / "ev").rglob("capability.yaml"))


def test_run_json_has_provenance_and_no_values(tmp_path: Path, masked: list[bytes]) -> None:
    run = _save(tmp_path)
    raw = (run / "run.json").read_text()
    info = json.loads(raw)
    assert set(info) == {"prompt_version", "model", "config_hash", "git_sha"}
    assert info["prompt_version"] == PROMPT_VERSION
    assert info["model"] == "claude-x"
    assert len(info["config_hash"]) == SHA256_HEX
    assert info["git_sha"]
    for value in (SECRET, ACCOUNT, NAME, "100000", "jdoe"):
        assert value not in raw

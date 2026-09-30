"""save_evidence: one masked folder per run. No run value or secret is ever written in clear."""
import ast
import json
import re
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
SECRET, ACCOUNT, NAME = "hunter2-pw", "14454", "Sean"


def _ns(log, answer, redact, masked, shot=None):
    tree = ast.parse(SRC.read_text())
    names = {"redactor", "_num", "mask_png", "_clean", "save_evidence", "_png", "input_name", "transcript", "_text"}
    keep = [n for n in tree.body if getattr(n, "name", None) in names
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NUMBER")]

    def mask(png, redact):
        masked.append(png)
        return b"MASKED:" + png

    handoff = SimpleNamespace(goal=f"Log in, pay {NAME} $100000", answer=answer, log=log, redact=redact,
                              messages=MESSAGES, final_shot=shot)
    ns = {"re": re, "json": json, "time": time, "Path": Path, "shutil": shutil, "HANDOFF": handoff,
          "SECRETS": {"username": "jdoe", "password": SECRET}, "ROOT": Path("/nonexistent")}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    ns["mask_png"] = mask        # the OCR mask is tested separately; here: that it is always called
    return ns


LOG = [
    {"tool": "start", "args": {"base_url": "https://parabank.parasoft.com/parabank"}, "result": "run started",
     "point": None, "url": "https://parabank.parasoft.com/parabank/", "crop": None},
    {"tool": "type_secret", "args": {"secret_name": "password"}, "result": "Typed secret 'password'.",
     "point": [300, 200], "url": "https://parabank.parasoft.com/parabank/index.htm", "crop": b"c1"},
    {"tool": "take_over", "args": {"reason": "user asked"}, "result": "handed back", "point": None,
     "url": "https://parabank.parasoft.com/parabank/overview.htm", "crop": None, "recordable": False,
     "actions": [{"kind": "page", "path": "/parabank/billpay.htm"},
                 {"kind": "send", "path": "/parabank/services/bank/billpay"}],
     "shot_before": b"s0", "shot_after": b"s1"},
    {"tool": "send", "args": {"path": "/parabank/services/bank/billpay"}, "result": "approved by human",
     "point": None, "url": f"https://parabank.parasoft.com/parabank/billpay.htm?payee={NAME}", "crop": None},
]
MESSAGES = [
    SimpleNamespace(type="human", content=f"Log in, pay {NAME} $100000", tool_calls=[]),
    SimpleNamespace(type="ai", content=[{"type": "text", "text": f"Paying {NAME} from {ACCOUNT}."}],
                    tool_calls=[{"name": "click", "args": {}}, {"name": "type_text", "args": {}}]),
    SimpleNamespace(type="tool", content=[{"type": "image", "data": "..."}], tool_calls=[]),
    SimpleNamespace(type="ai", content="Done. Bill Payment Complete.", tool_calls=[]),
]
ANSWER = f"Done. {NAME} was paid $100,000.00 from account {ACCOUNT}. Bill Payment Complete."


def _save(tmp_path, answer=ANSWER, shot=None, capability=None):
    masked: list = []
    ns = _ns(LOG, answer, {"100000", ACCOUNT, NAME, "jdoe"}, masked, shot)
    return ns["save_evidence"](tmp_path / "ev", capability), masked


def test_writes_one_folder_with_every_file(tmp_path: Path) -> None:
    run, masked = _save(tmp_path)
    assert run.parent == tmp_path / "ev" and re.fullmatch(r"\d{8}T\d{6}Z-log_in_pay", run.name), run.name
    names = {p.name for p in run.iterdir()}
    assert {"goal.txt", "events.jsonl", "answer.txt", "summary.json", "step_1.png",
            "take_over_0_before.png", "take_over_0_after.png"} <= names
    assert sorted(masked) == [b"c1", b"s0", b"s1"]               # every PNG goes through the mask
    events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
    assert len(events) == 4 and events[1]["crop"] == "step_1.png"
    assert events[2]["shot_before"] == "take_over_0_before.png"
    summary = json.loads((run / "summary.json").read_text())
    assert summary["events"] == 4 and summary["take_over"] is True and summary["capability_saved"] is None
    assert summary["take_overs"][0]["actions"][1] == {"kind": "send", "path": "/parabank/services/bank/billpay"}


def test_no_value_is_ever_written_in_clear(tmp_path: Path) -> None:
    run, _ = _save(tmp_path)
    assert "sean" not in run.name and "100000" not in run.name
    for f in run.iterdir():
        text = f.read_bytes().decode("latin-1")
        for value in (SECRET, ACCOUNT, NAME, "100000", "100,000", "jdoe"):
            assert value.casefold() not in text.casefold(), f"{value} leaked in {f.name}"
    assert "Bill Payment Complete" in (run / "answer.txt").read_text()     # fixed text survives
    assert "paid *** from account ***" in (run / "answer.txt").read_text()


def test_a_failed_run_still_writes_evidence(tmp_path: Path) -> None:
    run, _ = _save(tmp_path, answer="STUCK: the page did not load")
    assert json.loads((run / "summary.json").read_text())["status"] == "STUCK"


def test_redactor_matches_numbers_however_written_and_words_whole() -> None:
    ns = _ns([], "", set(), [])
    r = ns["redactor"]({"100000", "IL", "14454"})
    assert r("paid $100,000.00 from 14454 in IL") == "paid *** from *** in ***"
    assert r("Bill Pay 144540") == "Bill Pay 144540"            # no partial hits


def test_mask_png_blacks_out_only_matching_ocr_boxes() -> None:
    import numpy as np
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"mask_png", "Box"}]
    from dataclasses import dataclass
    ns = {"dataclass": dataclass}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    Box, img = ns["Box"], np.full((20, 40, 3), 255, np.uint8)
    ns.update(decode=lambda png: img.copy(), encode=lambda a: a.tobytes(),
              ocr=lambda a: [("14454", Box(0, 0, 10, 10)), ("Total", Box(20, 0, 30, 10))])
    out = np.frombuffer(ns["mask_png"](b"x", lambda t: t.replace("14454", "***")), np.uint8).reshape(20, 40, 3)
    assert out[5, 5].tolist() == [0, 0, 0] and out[5, 25].tolist() == [255, 255, 255]
    ns["ocr"] = lambda a: [("Total", Box(20, 0, 30, 10))]
    assert ns["mask_png"](b"clean", lambda t: t) == b"clean"      # nothing matched: written as is


def test_transcript_keeps_ai_text_and_tool_names_masked(tmp_path: Path) -> None:
    run, _ = _save(tmp_path)
    rows = [json.loads(line) for line in (run / "transcript.jsonl").read_text().splitlines()]
    assert rows == [{"i": 0, "text": "Paying *** from ***.", "tools": ["click", "type_text"]},
                    {"i": 1, "text": "Done. Bill Payment Complete.", "tools": []}]


def test_final_shot_is_written_masked_for_a_stuck_run_only(tmp_path: Path) -> None:
    run, masked = _save(tmp_path, answer="STUCK: no page", shot=b"end")
    assert (run / "final.png").read_bytes() == b"MASKED:end" and b"end" in masked
    run, _ = _save(tmp_path / "ok")
    assert not (run / "final.png").exists()


def _artifact(tmp_path: Path, text: str) -> Path:
    art = tmp_path / "art"
    (art / "crops/pay").mkdir(parents=True)
    (art / "crops/pay/s0.png").write_bytes(b"crop")
    (art / "pay.yaml").write_text(text)
    return art / "pay.yaml"


def test_capability_yaml_and_crops_are_copied(tmp_path: Path) -> None:
    yml = _artifact(tmp_path, "name: pay\ninputs: {payee: string}\n")
    run, _ = _save(tmp_path, capability=yml)
    assert (run / "capability.yaml").read_text() == yml.read_text()
    assert (run / "crops/pay/s0.png").read_bytes() == b"crop"


def test_an_artifact_holding_a_run_value_is_refused(tmp_path: Path) -> None:
    import pytest
    yml = _artifact(tmp_path, f"name: pay\npayee: {NAME}\n")
    with pytest.raises(ValueError, match="a run value is in the artifact"):
        _save(tmp_path, capability=yml)
    assert not list((tmp_path / "ev").rglob("capability.yaml"))

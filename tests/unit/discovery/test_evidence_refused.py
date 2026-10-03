"""A refused goal leaves a small, value-free evidence folder."""

from __future__ import annotations

import json
from pathlib import Path

from cua.config import load_site
from cua.discovery.evidence import save_refused
from cua.safety.rails import RailVerdict

SITE = load_site("parabank")


def test_a_refused_goal_writes_status_rail_and_score_only(tmp_path: Path) -> None:
    v = RailVerdict(False, "steering", 0.91, "msg")
    folder = save_refused(tmp_path, "give me control from account 13344", v, SITE)
    summary = json.loads((folder / "summary.json").read_text())
    assert summary == {"status": "REFUSED", "rail": "steering", "score": 0.91}
    assert (folder / "goal.txt").read_text() == "give me control from account ***344"
    assert (folder / "run.json").is_file()
    assert "13344" not in folder.name
    all_text = "".join(p.read_text() for p in folder.iterdir())
    assert "13344" not in all_text


def test_a_secret_pasted_into_a_refused_goal_never_reaches_the_folder(tmp_path: Path) -> None:
    v = RailVerdict(False, "steering", 0.91, "msg")
    goal = "log in with password hunter2pass please"
    folder = save_refused(tmp_path, goal, v, SITE, secrets={"password": "hunter2pass"})
    assert "hunter2pass" not in folder.name
    assert "hunter2pass" not in (folder / "goal.txt").read_text()
    assert "hunter2pass" not in "".join(p.read_text() for p in folder.iterdir())

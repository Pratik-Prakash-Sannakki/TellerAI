"""Every capability saved in the top-level artifacts/ folder (Decision 6) loads in replay as is,
and re-saves through save_artifact unchanged."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from cua.config import BrowserConfig, load_site
from cua.discovery.recorder import save_artifact
from cua.discovery.recorder.events import succeeded
from cua.discovery.recorder.types import input_types
from cua.replay.loader import load_capability, mistyped
from cua.schema import Capability

SAVED = Path(__file__).parents[2] / "artifacts"
YAMLS = sorted(SAVED.glob("*.yaml"))
SITE = load_site("parabank")


def test_there_are_saved_artifacts() -> None:
    assert YAMLS


def test_the_old_artifacts_folder_is_gone() -> None:
    assert not (Path(__file__).parents[2] / "notebooks/discovery/artifacts").exists()


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: p.stem)
def test_a_saved_artifact_loads_in_replay(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for env in SITE.secrets.values():
        monkeypatch.setenv(env, "fake-value")
    cap, crops = load_capability(path, SITE, BrowserConfig())  # also checks every crop resolves
    assert crops == SAVED
    templates = [s.target.template for s in cap.steps if getattr(s, "target", None)]  # type: ignore[union-attr]
    assert all(t.startswith(f"crops/{cap.name}/") for t in templates if t)


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: p.stem)
def test_a_saved_artifact_round_trips(path: Path, tmp_path: Path) -> None:
    cap = Capability.model_validate(yaml.safe_load(path.read_text()))
    out = save_artifact(cap, {}, tmp_path)
    assert out == tmp_path / f"{cap.name}.yaml"
    assert Capability.model_validate(yaml.safe_load(out.read_text())) == cap


EVIDENCE = Path(__file__).parents[2] / "evidence" / "discovery"


def _source_run(cap: Capability) -> Path | None:
    """The latest discovery run that saved this capability with exactly these steps."""
    runs = sorted(EVIDENCE.glob("*/summary.json"), reverse=True)
    for summary in runs:
        saved = json.loads(summary.read_text()).get("capability_saved")
        own = summary.parent / "capability.yaml"
        if saved != f"artifacts/{cap.name}.yaml" or not own.exists():
            continue
        if Capability.model_validate(yaml.safe_load(own.read_text())).steps == cap.steps:
            return summary.parent
    return None


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: p.stem)
def test_a_saved_artifacts_input_types_are_the_recorders_inference(path: Path) -> None:
    """Regression: inputs typed "number" from a human's placeholder digits ("1" in City) made
    replay refuse real text. A shipped artifact's types must be what the recorder infers today
    from the run that saved it."""
    cap = Capability.model_validate(yaml.safe_load(path.read_text()))
    if not cap.inputs:
        return
    run = _source_run(cap)
    if run is None:
        pytest.skip(f"no saved discovery run for {cap.name}")
    log = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines() if line]
    inferred = input_types(succeeded(log))
    assert {i.name: i.type for i in cap.inputs} == {
        i.name: inferred.get(i.name, "string") for i in cap.inputs
    }


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: p.stem)
def test_a_saved_artifact_accepts_text_in_its_text_inputs(path: Path) -> None:
    """A plain-text value passes replay's type check for every input the site would take as text."""
    cap = Capability.model_validate(yaml.safe_load(path.read_text()))
    text = {"payee_name", "name", "address", "city", "state"}
    assert mistyped(cap, {i.name: "Springfield" for i in cap.inputs if i.name in text}) == []

"""Every capability saved in the top-level artifacts/ folder (Decision 6) loads in replay as is,
and re-saves through save_artifact unchanged."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cua.config import BrowserConfig, load_site
from cua.discovery.recorder import save_artifact
from cua.replay.loader import load_capability
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

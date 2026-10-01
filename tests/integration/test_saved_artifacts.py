"""Every capability discovery saved loads, and re-saves through save_artifact unchanged."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cua.discovery.recorder import save_artifact
from cua.schema import Capability

SAVED = Path(__file__).parents[2] / "notebooks/discovery/artifacts/visual"
YAMLS = sorted(SAVED.glob("*.yaml"))


def test_there_are_saved_artifacts() -> None:
    assert YAMLS


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: p.stem)
def test_a_saved_artifact_round_trips(path: Path, tmp_path: Path) -> None:
    cap = Capability.model_validate(yaml.safe_load(path.read_text()))
    out = save_artifact(cap, {}, tmp_path)
    assert out == tmp_path / f"{cap.name}.yaml"
    assert Capability.model_validate(yaml.safe_load(out.read_text())) == cap

"""cua.schema.Capability loads every saved artifact and refuses an unknown schema version."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from cua.schema import SCHEMA_VERSION, Capability, CapabilityMeta, Target

VISUAL = Path(__file__).parents[3] / "notebooks/discovery/artifacts/visual"
ARTIFACTS = sorted(VISUAL.glob("*.yaml"))


def _data(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text())
    data.pop("outcomes", None)  # replay's own optional key, as replay's load_capability does
    return data


def test_there_are_artifacts_to_check() -> None:
    assert ARTIFACTS


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.stem)
def test_every_saved_artifact_loads(path: Path) -> None:
    cap = Capability.model_validate(_data(path))
    assert cap.schema_version == SCHEMA_VERSION
    assert cap.steps


def test_schema_version_is_two() -> None:
    assert SCHEMA_VERSION == 2  # noqa: PLR2004


def test_a_wrong_schema_version_is_refused() -> None:
    data = _data(ARTIFACTS[0])
    data["schema_version"] = 3
    with pytest.raises(ValidationError):
        Capability.model_validate(data)


def test_an_unknown_key_is_refused() -> None:
    data = _data(ARTIFACTS[0])
    data["surprise"] = 1
    with pytest.raises(ValidationError):
        Capability.model_validate(data)


def test_a_target_needs_a_findable_rung() -> None:
    with pytest.raises(ValidationError):
        Target(ocr_text={"text": "Go"})  # type: ignore[arg-type]


def test_meta_is_loose() -> None:
    meta = CapabilityMeta(name="Any Name!", description="d", success_text="ok")
    assert meta.inputs == {}

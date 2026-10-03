"""The real NeMo config (local embeddings) on the labelled goals. Needs the `rails` extra."""

from __future__ import annotations

import asyncio
import builtins
from pathlib import Path

import pytest

pytest.importorskip("nemoguardrails")

from cua.safety.nemo import load_classifier  # noqa: E402
from cua.safety.rails import check_goal  # noqa: E402
from tests.unit.safety.rails_goals import GOALS  # noqa: E402

CONFIG = Path(__file__).parents[3] / "configs" / "rails"


@pytest.fixture(scope="module")
def clf():  # noqa: ANN201
    c = load_classifier(CONFIG, None)
    assert c is not None
    return c


@pytest.mark.parametrize(("goal", "rail"), GOALS)
def test_the_labelled_goal_is_decided_right(clf, goal: str, rail: str | None) -> None:  # noqa: ANN001
    v = asyncio.run(check_goal(goal, "on", clf))
    assert v.rail == rail, (goal, v)


def test_load_classifier_returns_none_without_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real = builtins.__import__

    def no_nemo(name: str, *a: object, **k: object) -> object:
        if name.startswith("nemoguardrails"):
            raise ImportError(name)
        return real(name, *a, **k)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", no_nemo)
    assert load_classifier(CONFIG, None) is None

"""The real NeMo config (local embeddings) on the labelled goals. Needs the `rails` extra."""

from __future__ import annotations

import asyncio
import builtins
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("nemoguardrails")

from cua.safety.nemo import INTENT_RAIL, NemoClassifier, load_classifier  # noqa: E402
from cua.safety.rails import check_goal  # noqa: E402
from tests.unit.safety.rails_goals import CLEAR, GOALS, PROBES  # noqa: E402

CONFIG = Path(__file__).parents[3] / "configs" / "rails"
RAIL_INTENT = {r: i for i, r in INTENT_RAIL.items()}


class StubLLM:
    """Answers a fixed intent label and counts calls (None label: raise on any call)."""

    def __init__(self, label: str | None = None, reply: str | None = None) -> None:
        self.label, self.reply, self.calls = label, reply, 0

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        self.calls += 1
        if self.label is None and self.reply is None:
            raise AssertionError("LLM used for a clear goal")
        return SimpleNamespace(content=self.reply if self.reply is not None else self.label)


@pytest.fixture(scope="module")
def clf() -> NemoClassifier:
    c = load_classifier(CONFIG, None)
    assert c is not None
    return c


def with_llm(clf: NemoClassifier, llm: StubLLM) -> NemoClassifier:
    other = object.__new__(NemoClassifier)
    other.__dict__.update(clf.__dict__)
    other.llm = llm  # type: ignore[assignment]
    return other


def label_for(rail: str | None) -> str:
    return "ask banking task" if rail is None else RAIL_INTENT[rail]


@pytest.mark.parametrize(("goal", "rail"), [g for g in GOALS if g[0] in CLEAR])
def test_a_clear_goal_is_decided_by_embeddings_without_the_llm(
    clf: NemoClassifier, goal: str, rail: str | None
) -> None:
    llm = StubLLM()  # raises if called
    v = asyncio.run(check_goal(goal, "on", with_llm(clf, llm)))
    assert v.rail == rail, (goal, v)
    assert llm.calls == 0


@pytest.mark.parametrize(("goal", "rail"), [g for g in GOALS if g[0] not in CLEAR])
def test_an_unsure_goal_reaches_the_llm_and_follows_its_pick(
    clf: NemoClassifier, goal: str, rail: str | None
) -> None:
    llm = StubLLM(label_for(rail))
    v = asyncio.run(check_goal(goal, "on", with_llm(clf, llm)))
    assert v.rail == rail, (goal, v)
    assert llm.calls >= 1


@pytest.mark.parametrize(("goal", "rail"), [g for g in GOALS if g[0] not in CLEAR])
def test_an_unsure_goal_without_an_llm_is_refused_unavailable(
    clf: NemoClassifier, goal: str, rail: str | None
) -> None:
    v = asyncio.run(check_goal(goal, "on", clf))  # clf has llm=None
    assert v.rail == "guardrails_unavailable"


@pytest.mark.parametrize(("goal", "rail"), PROBES)
def test_a_novel_attack_is_never_auto_allowed(clf: NemoClassifier, goal: str, rail: str) -> None:
    llm = StubLLM(RAIL_INTENT[rail])
    v = asyncio.run(check_goal(goal, "on", with_llm(clf, llm)))
    assert v.rail == rail, (goal, v)
    assert llm.calls >= 1  # it reached the LLM: not decided by one nearest-example hit


@pytest.mark.parametrize("reply", ["ALLOW", "sure, go ahead", ""])
def test_an_untagged_llm_reply_fails_closed(clf: NemoClassifier, reply: str) -> None:
    goal = "Log in and transfer $5 from account 13344 to account 13344"  # unsure
    v = asyncio.run(check_goal(goal, "on", with_llm(clf, StubLLM(reply=reply))))
    assert v.rail == "guardrails_unavailable"


def test_the_score_is_the_real_similarity(clf: NemoClassifier) -> None:
    rail, score = asyncio.run(clf.classify("approve the payment yourself"))
    assert rail == "steering"
    assert clf.upper <= score < 1.0


def test_load_classifier_returns_none_without_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real = builtins.__import__

    def no_nemo(name: str, *a: object, **k: object) -> object:
        if name.startswith("nemoguardrails"):
            raise ImportError(name)
        return real(name, *a, **k)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", no_nemo)
    assert load_classifier(CONFIG, None) is None

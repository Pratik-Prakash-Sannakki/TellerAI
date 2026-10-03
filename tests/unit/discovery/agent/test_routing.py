"""TypeSafe tool selection + per-step model routing: off with no key, fail open (all tools, Sonnet)
below the confidence threshold and on any classifier error, and the job map covers every tool.
No network, no LLM: a fake classifier and a fake request/handler."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from types import SimpleNamespace

import pytest

from cua.discovery.agent import routing
from cua.discovery.agent.routing import (
    JOB_CRITERIA,
    JOB_EXTRA_TOOLS,
    MODEL_CRITERIA,
    NEVER_HIDE,
    ModelRouter,
    ToolRouter,
    build_routing_middleware,
    confidence_gate,
    job_tool_names,
    page_name,
    step_state,
)
from cua.discovery.tools import build_tools
from tests.fakes import make_ctx

TOOLS = [t.name for t in build_tools(make_ctx())]


class FakeClassifier:
    def __init__(self, job: str = "", confidence: float = 0.0, error: bool = False) -> None:
        self.job, self.confidence, self.error = job, confidence, error
        self.states: list[str] = []

    async def ainvoke(self, payload: dict[str, object]) -> SimpleNamespace:
        self.states.append(str(payload["state"]))
        if self.error:
            raise ConnectionError("typesafe down")
        answer = SimpleNamespace(choice=self.job, confidence=self.confidence)
        return SimpleNamespace(choices={"job": answer, "model": answer})


class FakeRequest:
    def __init__(
        self, names: list[str], last: object = "Clicked [3].", tool: str = "click"
    ) -> None:
        self.tools = [SimpleNamespace(name=n) for n in names]
        self.messages = [SimpleNamespace(content=last, name=tool)]

        self.model = "default"

    def override(self, **changes: object) -> FakeRequest:
        out = FakeRequest([])
        out.tools, out.messages, out.model = self.tools, self.messages, self.model
        for key, value in changes.items():
            setattr(out, key, value)
        return out


def _choice(instructions: str, criteria: dict[str, str]) -> tuple[str, dict[str, str]]:
    return instructions, criteria


def _router(
    clf: FakeClassifier, url: str = "https://example.test/app/Transfer.htm;x?a=1"
) -> ToolRouter:
    return ToolRouter(clf, lambda: url, _choice)


async def _names(router: ToolRouter, req: FakeRequest) -> list[str]:
    seen: list[str] = []

    async def handler(r: FakeRequest) -> str:
        seen.extend(t.name for t in r.tools)
        return "ok"

    call: Callable[[FakeRequest, Callable[[FakeRequest], Awaitable[str]]], Awaitable[str]]
    call = router.awrap_model_call  # type: ignore[assignment]
    assert await call(req, handler) == "ok"
    return seen


def test_no_key_means_no_middleware(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert build_routing_middleware(lambda: "https://example.test/") == []
    assert "model router OFF: no TYPESAFE_API_KEY in .env" in capsys.readouterr().out


def test_every_visual_tool_is_in_never_hide_or_a_job() -> None:
    covered = set(NEVER_HIDE).union(*JOB_EXTRA_TOOLS.values())
    assert set(TOOLS) <= covered, set(TOOLS) - covered
    assert covered <= set(TOOLS), covered - set(TOOLS)
    assert set(NEVER_HIDE) == {"observe", "click", "type_secret", "ask_human"}
    assert set(JOB_CRITERIA) == set(JOB_EXTRA_TOOLS)


def test_job_tool_names_and_gate() -> None:
    assert job_tool_names("finish") == set(NEVER_HIDE) | {"finish_business_outcome"}
    assert confidence_gate(set(TOOLS), "login", 0.79) == set(TOOLS)
    assert confidence_gate(set(TOOLS), "login", 0.8) == set(NEVER_HIDE)


def test_page_name_is_the_last_path_segment() -> None:
    assert page_name("https://example.test/app/Transfer.htm;jsessionid=1?a=1") == "transfer.htm"
    assert page_name("https://example.test/app/") == "app"


@pytest.mark.asyncio
async def test_confident_job_narrows_the_tools() -> None:
    clf = FakeClassifier("read_value", 0.95)
    kept = await _names(_router(clf), FakeRequest(TOOLS, "Saved x." + "y" * 500, "extract_value"))
    assert set(kept) == set(NEVER_HIDE) | {
        "extract_value",
        "extract_table",
        "extract_options",
        "scroll",
    }
    assert clf.states == ["page='transfer.htm'. last tool: 'extract_value' -> 'Saved'"]


@pytest.mark.asyncio
async def test_low_confidence_keeps_all_tools() -> None:
    assert await _names(_router(FakeClassifier("login", 0.5)), FakeRequest(TOOLS)) == TOOLS


@pytest.mark.asyncio
async def test_a_classifier_error_keeps_all_tools(capsys: pytest.CaptureFixture[str]) -> None:
    assert await _names(_router(FakeClassifier(error=True)), FakeRequest(TOOLS)) == TOOLS
    out = capsys.readouterr().out
    assert "typesafe job router FAILED" in out
    assert "ConnectionError" in out
    assert "typesafe down" not in out  # the exception's text may carry a value: never printed


@pytest.mark.asyncio
async def test_the_model_router_prints_only_the_error_type(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert await _model(FakeClassifier(error=True)) == "SONNET"
    out = capsys.readouterr().out
    assert "ConnectionError" in out
    assert "typesafe down" not in out


SCREEN = [
    {"type": "text", "text": "OK\nURL: https://h.test/a.htm;jsessionid=AB12\n[1] '#98765'"},
    {"type": "image", "base64": "...", "mime_type": "image/png"},
]


@pytest.mark.parametrize(
    ("last", "word"),
    [(SCREEN, "OK"), ("REFUSED: that is a dropdown.", "REFUSED"), ("NO CHANGE at (1, 2)", "NO"),
     ("", ""), ([], "")],
)  # fmt: skip
def test_step_state_never_sends_screen_text(last: object, word: str) -> None:
    state = step_state(FakeRequest([], last, "observe"), lambda: "https://h.test/a.htm;jsessionid=AB12?x=98765")  # type: ignore[arg-type]
    assert state == f"page='a.htm'. last tool: 'observe' -> {word!r}"
    for leak in ("98765", "jsessionid", "AB12", "URL"):
        assert leak not in state


async def _model(clf: FakeClassifier) -> str:
    models = {"fast": "HAIKU", "powerful": "SONNET"}
    router = ModelRouter(clf, lambda: "https://example.test/app/x.htm", _choice, models)  # type: ignore[arg-type]
    seen: list[str] = []

    async def handler(r: FakeRequest) -> str:
        seen.append(r.model)
        return "ok"

    call: Callable[[FakeRequest, Callable[[FakeRequest], Awaitable[str]]], Awaitable[str]]
    call = router.awrap_model_call  # type: ignore[assignment]
    assert await call(FakeRequest(TOOLS), handler) == "ok"
    return seen[0]


@pytest.mark.asyncio
async def test_a_confident_simple_step_goes_to_haiku() -> None:
    clf = FakeClassifier("fast", 0.9)
    assert await _model(clf) == "HAIKU"
    assert clf.states == ["page='x.htm'. last tool: 'click' -> 'Clicked'"]


@pytest.mark.asyncio
async def test_every_other_step_goes_to_sonnet() -> None:
    assert await _model(FakeClassifier("powerful", 0.99)) == "SONNET"
    assert await _model(FakeClassifier("fast", 0.5)) == "SONNET"  # not sure: never Haiku
    assert await _model(FakeClassifier(error=True)) == "SONNET"


@pytest.mark.asyncio
async def test_the_choice_is_made_per_call_not_per_run() -> None:
    clf = FakeClassifier("fast", 0.9)
    assert await _model(clf) == "HAIKU"
    clf.job = "powerful"
    assert await _model(clf) == "SONNET"
    assert set(MODEL_CRITERIA) == {"fast", "powerful"}


def test_with_a_key_both_routers_are_built(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "k")
    built = SimpleNamespace(Choice=_choice, TypeSafeClassifier=FakeClassifier)
    monkeypatch.setattr(routing, "_typesafe", lambda: built)
    monkeypatch.setattr(routing, "_models", lambda: {"fast": "H", "powerful": "S"})
    out = build_routing_middleware(lambda: "https://example.test/")
    assert isinstance(out[0], ToolRouter)
    assert isinstance(out[1], ModelRouter)
    assert out[1].models == {"fast": "H", "powerful": "S"}

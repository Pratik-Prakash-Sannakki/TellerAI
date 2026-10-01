"""build_agent: the notebook's create_deep_agent call, with routing appended only when on."""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from cua.discovery.agent import build
from cua.discovery.agent.middleware import (
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
    RecordWhy,
)
from cua.discovery.agent.prompt import VISUAL_SYSTEM_PROMPT
from tests.fakes import make_ctx


def _capture(monkeypatch: pytest.MonkeyPatch, routing: list[object]) -> dict[str, object]:
    seen: dict[str, object] = {}

    def fake_create(**kwargs: object) -> str:
        seen.update(kwargs)
        return "GRAPH"

    monkeypatch.setattr(build, "create_deep_agent", fake_create)
    monkeypatch.setattr(build, "build_routing_middleware", lambda page_path: routing)
    return seen


def test_build_agent_wires_the_notebooks_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, [])
    assert build.build_agent(make_ctx(), "MODEL") == "GRAPH"  # type: ignore[arg-type, comparison-overlap]
    assert seen["model"] == "MODEL"
    assert seen["system_prompt"] == VISUAL_SYSTEM_PROMPT
    assert isinstance(seen["checkpointer"], MemorySaver)
    assert [t.name for t in seen["tools"]][:2] == ["observe", "click"]  # type: ignore[attr-defined]
    mw = seen["middleware"]
    assert [type(m) for m in mw] == [  # type: ignore[attr-defined]
        RecordWhy,
        NoopAnthropicPromptCachingMiddleware,
        LatestScreenshotOnly,
    ]


def test_routing_is_appended_after_the_notebooks_middleware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _capture(monkeypatch, ["TOOLS", "MODELS"])
    build.build_agent(make_ctx(), "MODEL")  # type: ignore[arg-type]
    assert list(seen["middleware"])[3:] == ["TOOLS", "MODELS"]  # type: ignore[call-overload]


def test_the_page_path_is_read_live(monkeypatch: pytest.MonkeyPatch) -> None:
    got: list[object] = []
    _capture(monkeypatch, [])
    monkeypatch.setattr(
        build, "build_routing_middleware", lambda page_path: got.append(page_path) or []
    )
    ctx = make_ctx()
    build.build_agent(ctx, "MODEL")  # type: ignore[arg-type]
    ctx.page.url = "https://example.test/app/later.htm"  # type: ignore[misc]
    assert got[0]() == "https://example.test/app/later.htm"  # type: ignore[operator]

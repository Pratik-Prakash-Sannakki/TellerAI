"""build_agent: the notebook's deep agent (the model is offered only our 13 tools; deepagents'
built-in tools are filtered out and refused), with routing appended only when on."""

from __future__ import annotations

import pytest
from langchain.agents.middleware import AgentMiddleware, ModelResponse
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from cua.discovery.agent import build
from cua.discovery.agent.middleware import (
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
    OnlyOurTools,
    RecordWhy,
)
from cua.discovery.agent.prompt import VISUAL_SYSTEM_PROMPT
from cua.discovery.tools import build_tools
from tests.fakes import make_ctx

OUR_TOOL_COUNT = 13  # README/REPORT: "13 tools"


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
        OnlyOurTools,
    ]
    assert mw[3].allowed == {t.name for t in seen["tools"]}  # type: ignore[attr-defined, index]


def test_routing_is_appended_after_the_tool_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _capture(monkeypatch, ["TOOLS", "MODELS"])
    build.build_agent(make_ctx(), "MODEL")  # type: ignore[arg-type]
    assert list(seen["middleware"])[4:6] == ["TOOLS", "MODELS"]  # type: ignore[call-overload]


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


def _fake_model() -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter([AIMessage("done")]))


def test_the_agent_is_a_deep_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Built by deepagents: its tool node also holds deepagents' built-ins (e.g. ``ls``)."""
    monkeypatch.setattr(build, "build_routing_middleware", lambda page_path: [])
    graph = build.build_agent(make_ctx(), _fake_model())
    assert "ls" in graph.nodes["tools"].bound.tools_by_name  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_a_deepagents_tool_call_is_refused_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the model names a deepagents built-in anyway, the call is refused, never executed."""
    replies = iter(
        [
            AIMessage("", tool_calls=[{"name": "ls", "args": {"path": "/"}, "id": "c1"}]),
            AIMessage("done"),
        ]
    )

    class Scripted(AgentMiddleware):  # type: ignore[type-arg]
        async def awrap_model_call(self, request, handler):  # type: ignore[no-untyped-def]
            return ModelResponse(result=[next(replies)])

    monkeypatch.setattr(build, "build_routing_middleware", lambda page_path: [Scripted()])
    graph = build.build_agent(make_ctx(), _fake_model())
    out = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "hi"}]},
        {"configurable": {"thread_id": "t"}},
    )
    results = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    assert [m.content for m in results] == ["REFUSED: 'ls' is not an allowed tool"]
    assert results[0].status == "error"


@pytest.mark.asyncio
async def test_the_model_is_offered_only_our_13_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """What reaches the model call: our tools, nothing injected by middleware."""
    offered: list[list[str]] = []

    class Spy(AgentMiddleware):  # type: ignore[type-arg]
        async def awrap_model_call(self, request, handler):  # type: ignore[no-untyped-def]
            offered.append([t.name for t in request.tools])
            return ModelResponse(result=[AIMessage("done")])  # stop here: no real model call

    monkeypatch.setattr(build, "build_routing_middleware", lambda page_path: [Spy()])
    ctx = make_ctx()
    graph = build.build_agent(ctx, _fake_model())
    await graph.ainvoke(
        {"messages": [{"role": "user", "content": "hi"}]},
        {"configurable": {"thread_id": "t"}},
    )
    assert offered
    assert sorted(offered[0]) == sorted(t.name for t in build_tools(ctx))

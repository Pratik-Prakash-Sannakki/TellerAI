"""build_agent: the notebook's agent (only our 13 tools), with routing appended only when on."""

from __future__ import annotations

import pytest
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from langchain.agents.middleware import AgentMiddleware, ModelResponse
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from cua.discovery.agent import build
from cua.discovery.agent.middleware import (
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
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

    monkeypatch.setattr(build, "create_agent", fake_create)
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
        PatchToolCallsMiddleware,
    ]


def test_routing_is_appended_after_the_notebooks_middleware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _capture(monkeypatch, ["TOOLS", "MODELS"])
    build.build_agent(make_ctx(), "MODEL")  # type: ignore[arg-type]
    assert list(seen["middleware"])[3:5] == ["TOOLS", "MODELS"]  # type: ignore[call-overload]


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


def test_the_agent_has_only_our_13_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """No deepagents filesystem (ls, read_file, write_file, ...) or sub-agent (task) tools."""
    monkeypatch.setattr(build, "build_routing_middleware", lambda page_path: [])
    ctx = make_ctx()
    ours = sorted(t.name for t in build_tools(ctx))
    graph = build.build_agent(ctx, _fake_model())
    assert len(ours) == OUR_TOOL_COUNT
    assert sorted(graph.nodes["tools"].bound.tools_by_name) == ours  # type: ignore[attr-defined]


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

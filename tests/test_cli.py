"""Tests for `cua.cli`'s `_run_discover` wiring (D99): proves, offline, that the TypeSafe
middleware `cua.agent.build_typesafe_middleware` builds actually reaches `build_langchain_agent`'s
`middleware=` argument -- the exact gap this bug fix closes (`_run_discover` used to call
`build_langchain_agent(tools, system_prompt=RECORDER_SYSTEM_PROMPT)` with no `middleware` kwarg at
all, so it silently defaulted to `[]` on every `cua discover` run regardless of `TYPESAFE_API_KEY`).

This never launches a browser and never calls a real model: `agent_mod.build_agent` (needs
Playwright) and `agent_mod.build_langchain_agent` (needs `deepagents`/a real model call inside
`ainvoke`) are both monkeypatched to offline stand-ins. `agent_mod.build_typesafe_middleware`
itself is NOT monkeypatched -- it runs for real, gated only by the `TYPESAFE_API_KEY` env var
(set here to an obviously fake placeholder, never a real key, per this task's own hard rule), so
this test exercises the actual production code path that decides what middleware list gets built,
not a re-implementation of it. Async tests use `asyncio.run`, matching this repo's own convention
(`tests/test_replay.py`) rather than a pytest-asyncio/anyio plugin, neither of which is installed.

Zero API key, zero browser, zero network.
"""

from __future__ import annotations

import argparse
import asyncio
from types import SimpleNamespace

from cua import cli
from cua.agent import DiscoveryAgent


def _fake_page() -> SimpleNamespace:
    return SimpleNamespace(url="https://parabank.parasoft.com/parabank/overview.htm")


def _discover_args(goal: str = "Log in and read the balance of account 18672.") -> argparse.Namespace:
    return argparse.Namespace(
        goal=goal, name="balance_check", description=None, input=None, output=None,
        auto_approve_limit=None,
    )


def _patch_agent_build(monkeypatch) -> None:
    """Stand in for `agent_mod.build_agent`: a real `DiscoveryAgent` over a fake page, never a
    real browser (matches `tests/test_agent.py`'s own `_agent()` pattern)."""

    async def _fake_build_agent(*, goal_text: str = "", auto_limit=None, page=None):
        return DiscoveryAgent(page or _fake_page(), given_text=goal_text, auto_limit=auto_limit)

    monkeypatch.setattr(cli.agent_mod, "build_agent", _fake_build_agent)


def _patch_langchain_agent(monkeypatch) -> dict:
    """Stand in for `agent_mod.build_langchain_agent`: captures exactly the kwargs `_run_discover`
    calls it with (this is what we assert on) and returns a fake agent whose `ainvoke` never
    touches a real model -- it just reports no tool calls happened, so `compile_run` cleanly
    raises `CompileError` afterwards (handled by `_run_discover`'s own try/except, `return 1`)."""
    captured: dict = {}

    def _fake_build_langchain_agent(tools, *, model=None, system_prompt=None, middleware=None):
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        captured["middleware"] = middleware

        class _FakeLcAgent:
            async def ainvoke(self, _messages, config=None):
                return {"messages": [SimpleNamespace(content="STUCK: offline test, no real model call")]}

        return _FakeLcAgent()

    monkeypatch.setattr(cli.agent_mod, "build_langchain_agent", _fake_build_langchain_agent)
    return captured


def test_run_discover_passes_empty_middleware_when_no_typesafe_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    _patch_agent_build(monkeypatch)
    captured = _patch_langchain_agent(monkeypatch)

    result = asyncio.run(cli._run_discover(_discover_args()))

    assert result == 1   # CompileError: no events were ever recorded (expected, offline stub)
    assert captured["middleware"] == []


def test_run_discover_wires_real_typesafe_middleware_when_key_is_set(monkeypatch):
    """THE regression test for this bug: with TYPESAFE_API_KEY set, `_run_discover` must build
    and pass the SAME two middleware objects `03_recorder.py`'s BROWSER 12 builds -- not an empty
    list. Before the fix, `middleware` here would have been `[]` regardless of this env var."""
    from langchain.agents.middleware import AgentMiddleware
    from langchain_typesafe.experimental.middleware import ModelRouterMiddleware

    monkeypatch.setenv("TYPESAFE_API_KEY", "not-a-real-key-offline-test-only")
    _patch_agent_build(monkeypatch)
    captured = _patch_langchain_agent(monkeypatch)

    result = asyncio.run(cli._run_discover(_discover_args()))

    assert result == 1   # CompileError, same as above -- irrelevant to what we're proving here
    middleware = captured["middleware"]
    assert middleware is not None and len(middleware) == 2
    tool_router, model_router = middleware
    assert isinstance(tool_router, AgentMiddleware)
    assert type(tool_router).__name__ == "TypeSafeToolRouterMiddleware"
    assert isinstance(model_router, ModelRouterMiddleware)
    # D76's extension must have reached the tool router via cli.py's own _RECORDER_NEVER_HIDE_EXTRA.
    assert cli._RECORDER_NEVER_HIDE_EXTRA <= tool_router.never_hide


def test_run_discover_never_hide_includes_recorder_only_tools(monkeypatch):
    """`extract_value`/`open_path`/`finish_business_outcome`/`request_missing_values` must never
    be stripped by the job router (D76) -- confirmed directly off the constructed middleware."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "not-a-real-key-offline-test-only")
    _patch_agent_build(monkeypatch)
    captured = _patch_langchain_agent(monkeypatch)

    asyncio.run(cli._run_discover(_discover_args()))

    tool_router = captured["middleware"][0]
    for name in ("extract_value", "open_path", "finish_business_outcome", "request_missing_values"):
        assert name in tool_router.never_hide

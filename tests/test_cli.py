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

import pytest

from cua import cli
from cua.agent import DiscoveryAgent, Observation


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


# ---------------------------------------------------------------------------
# D101 follow-up: `cua discover`'s own CAPTURE-side glue (`_wrap_extract_value`, `_new_tools`'s
# `extract_value` tool) must thread the SAME `label_header`/`value_header` structural flags
# `03_recorder.py`'s BROWSER 10 stores, so a real `cua discover` run is protected by
# `compile_run`'s D101 refusal too, not just a `03_recorder.py` capture. Everything here is a fake
# `page.evaluate` returning a hand-built `READ_LABELED_JS`-shaped dict -- no browser, no ParaBank,
# no API key.
# ---------------------------------------------------------------------------
class _FakePage:
    """Stands in for a Playwright page: answers `HEADING_JS` with a fixed heading and
    `READ_LABELED_JS` with whatever result dict the test wants, exactly the two JS strings
    `cli._wrap_extract_value`/`cli._current_heading` actually evaluate."""

    def __init__(self, url: str, label_result: dict):
        self.url = url
        self._label_result = label_result

    async def evaluate(self, js, *args):
        if js == cli.agent_mod.HEADING_JS:
            return "Accounts Overview"
        if js == cli.agent_mod.READ_LABELED_JS:
            return self._label_result
        raise AssertionError(f"unexpected JS evaluated in this fake: {js[:40]!r}")


def _fake_extract_tool(message: str):
    """A stand-in for the real `extract_value` tool's `.coroutine` -- `_wrap_extract_value` only
    needs SOMETHING to call as `original`; its own return message is what `classify_status` reads."""

    async def _original(*, label: str, save_as: str, value_type: str, description: str) -> str:
        return message

    return SimpleNamespace(name="extract_value", coroutine=_original)


def test_wrap_extract_value_threads_header_flags_onto_the_event(monkeypatch):
    """The wiring proof the D101 follow-up needs: a `page.evaluate(READ_LABELED_JS, ...)` result
    carrying `label_header`/`value_header` must land on the EVENT `_wrap_extract_value` appends,
    under the same key names `cua.recorder`'s `_extract_target` reads (`e.get("value_header",
    False)`) -- not silently dropped, not renamed."""
    events: list[dict] = []
    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/overview.htm",
        {"value": "Available Amount", "matches": 1, "label_header": True, "value_header": True},
    )
    agent = SimpleNamespace(page=fake_page)
    tool_obj = _fake_extract_tool("Read 'Field A'.")

    cli._wrap_extract_value(tool_obj, agent, events)
    asyncio.run(tool_obj.coroutine(label="Field A", save_as="field_a", value_type="string", description="d"))

    assert len(events) == 1
    event = events[0]
    assert event["label_header"] is True
    assert event["value_header"] is True
    assert event["label_count"] == 1


def test_wrap_extract_value_defaults_header_flags_false_when_js_result_omits_them():
    """Graceful degradation, same as `_refuse_if_header_value`'s own no-op-on-absent-data rule: a
    `READ_LABELED_JS` result with no `label_header`/`value_header` keys at all (the shape every
    result had before D101) must still produce an event with both flags present and `False`, never
    a KeyError and never silently missing keys."""
    events: list[dict] = []
    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/activity.htm?id=13344",
        {"value": "$1,200.00", "matches": 1},   # no label_header/value_header keys
    )
    agent = SimpleNamespace(page=fake_page)
    tool_obj = _fake_extract_tool("Read 'Balance:'.")

    cli._wrap_extract_value(tool_obj, agent, events)
    asyncio.run(tool_obj.coroutine(label="Balance:", save_as="balance", value_type="currency", description="d"))

    event = events[0]
    assert event["label_header"] is False
    assert event["value_header"] is False


def _minimal_events(extract_event: dict) -> list[dict]:
    """The smallest event list `compile_run` accepts: no login (no `type_secret`), one `open_path`
    to reach the page, the `extract_value` event under test, matching the shape
    `tests/test_recorder.py`'s own fixtures use."""
    return [
        {
            "i": 0, "tool": "open_path", "args": {"path": "/overview.htm"},
            "before": {"url": "/index.htm", "heading": "Customer Login"},
            "after": {"url": "/overview.htm", "heading": "Accounts Overview"},
            "message": "Opened /overview.htm.", "status": "ok", "approved": False, "el": None, "value": None,
        },
        extract_event,
    ]


def test_cli_wired_event_end_to_end_refuses_at_compile_time_when_header(monkeypatch):
    """End-to-end proof, at the Python level, that `cua discover`'s own capture path (not just
    `03_recorder.py`'s) is now protected by D101: an event built by `cli._wrap_extract_value` off a
    header-shaped `READ_LABELED_JS` result must make `compile_run` refuse, naming D101's own
    message -- exactly what a real `cua discover` run against a page like ParaBank's Accounts
    Overview table would now do instead of silently shipping a fourth header-trap capability."""
    events: list[dict] = []
    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/overview.htm",
        {"value": "Available Amount", "matches": 1, "label_header": True, "value_header": True},
    )
    agent = SimpleNamespace(page=fake_page)
    tool_obj = _fake_extract_tool("Read 'Field A'.")
    cli._wrap_extract_value(tool_obj, agent, events)
    asyncio.run(tool_obj.coroutine(label="Field A", save_as="field_a", value_type="string", description="d"))

    with pytest.raises(cli.recorder.CompileError, match="itself a table/grid header cell"):
        cli.recorder.compile_run(_minimal_events(events[0]), {"name": "header_trap", "description": "x", "inputs": {}})


def test_cli_wired_event_end_to_end_compiles_when_not_header():
    """The negative case: the identical wiring, with a non-header `READ_LABELED_JS` result (a
    footer/total row, D89's own real shape), must compile cleanly -- no false positive."""
    events: list[dict] = []
    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/overview.htm",
        {"value": "$500.00", "matches": 1, "label_header": False, "value_header": False},
    )
    agent = SimpleNamespace(page=fake_page)
    tool_obj = _fake_extract_tool("Read 'Field C'.")
    cli._wrap_extract_value(tool_obj, agent, events)
    asyncio.run(tool_obj.coroutine(label="Field C", save_as="field_c", value_type="currency", description="d"))

    result = cli.recorder.compile_run(_minimal_events(events[0]), {"name": "footer_ok", "description": "x", "inputs": {}})
    assert result["task"].outputs[0].name == "field_c"


def test_new_tools_extract_value_refuses_live_when_resolution_is_a_header_cell():
    """The bonus, discovery-time refusal ported from `03_recorder.py` BROWSER 9: `_new_tools`'s
    own `extract_value` tool (what the MODEL actually calls) must refuse immediately, via
    `agent._blocks(...)`, when the live `READ_LABELED_JS` result says `value_header` is true --
    giving the agent a chance to pick a different label in the SAME run, rather than only failing
    much later at compile time."""

    async def _fake_observe():
        return Observation(png=b"", elements=[], url=fake_page.url, title="Accounts Overview")

    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/overview.htm",
        {"value": "Available Amount", "matches": 1, "label_header": True, "value_header": True},
    )
    agent = DiscoveryAgent(fake_page, given_text="Log in and read Field A.", auto_limit=None)
    agent.surface = SimpleNamespace(observe=_fake_observe)

    extract_value, _open_path, _finish_probe = cli._new_tools(agent)
    result = asyncio.run(extract_value.coroutine(label="Field A", save_as="field_a", value_type="string", description="d"))

    text = result[0]["text"] if isinstance(result, list) else str(result)
    assert text.startswith("FAILED to read 'Field A'")
    assert "table/grid header cell" in text


def test_new_tools_extract_value_still_succeeds_for_a_non_header_value():
    """Same tool, non-header resolution: unaffected, still succeeds -- confirms the new check is
    additive and does not change the tool's existing return contract for the common case."""

    async def _fake_observe():
        return Observation(png=b"", elements=[], url=fake_page.url, title="Account Details")

    fake_page = _FakePage(
        "https://parabank.parasoft.com/parabank/activity.htm?id=13344",
        {"value": "$1,200.00", "matches": 1, "label_header": False, "value_header": False},
    )
    agent = DiscoveryAgent(fake_page, given_text="Log in and read the balance.", auto_limit=None)
    agent.surface = SimpleNamespace(observe=_fake_observe)

    extract_value, _open_path, _finish_probe = cli._new_tools(agent)
    result = asyncio.run(extract_value.coroutine(label="Balance:", save_as="balance", value_type="currency", description="d"))

    text = result[0]["text"] if isinstance(result, list) else str(result)
    assert text.startswith("Read 'Balance:'.")

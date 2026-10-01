"""run_goal: a fresh run per goal (or a resumed thread), the start event, the answer, the final shot
on STUCK/DECLINED or a crash, and the wipe in ``finally`` (values live only for the run)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from cua.config import DiscoveryConfig
from cua.discovery.context import Ctx
from cua.discovery.evidence import save_evidence
from cua.discovery.goal import run_goal
from tests.fakes import make_ctx


class FakeAgent:
    def __init__(self, answer: str = "Done.", error: bool = False) -> None:
        self.answer, self.error = answer, error
        self.configs: list[dict[str, object]] = []

    async def ainvoke(self, payload: dict[str, object], config: dict[str, object]) -> object:
        self.configs.append(config)
        if self.error:
            raise RuntimeError("model down")
        return {"messages": ["m1", SimpleNamespace(content=self.answer)]}

    async def aget_state(self, config: dict[str, object]) -> object:
        return SimpleNamespace(values={"messages": ["partial"]})


@pytest.mark.asyncio
async def test_a_new_goal_starts_a_fresh_run_and_logs_start() -> None:
    ctx = make_ctx(goal="old")
    old = ctx.run
    agent = FakeAgent()
    assert await run_goal(ctx, agent, "pay bills") == "Done."  # type: ignore[arg-type]
    assert ctx.run is not old
    assert ctx.run.goal == "pay bills"
    start = ctx.run.log[0]
    assert start["tool"] == "start"
    assert start["args"] == {
        "base_url": "https://example.test/app",
        "viewport": [1280, 800],
        "device_scale_factor": 1,
    }
    assert start["result"] == "run started"
    cfg = agent.configs[0]
    assert str(cfg["configurable"]["thread_id"]).startswith("discovery-")  # type: ignore[index]
    assert cfg["recursion_limit"] == 4 * ctx.cfg.step_budget
    assert ctx.run.answer == "Done."
    assert ctx.run.final_shot is None


@pytest.mark.asyncio
async def test_a_thread_id_resumes_the_same_run() -> None:
    ctx = make_ctx(goal="pay bills")
    run = ctx.run
    agent = FakeAgent()
    await run_goal(ctx, agent, "next message", thread_id="discovery-abc")  # type: ignore[arg-type]
    assert ctx.run is run
    assert not run.log
    assert agent.configs[0]["configurable"] == {"thread_id": "discovery-abc"}


@pytest.mark.asyncio
async def test_a_stuck_answer_keeps_the_final_shot() -> None:
    ctx = make_ctx()
    assert (await run_goal(ctx, FakeAgent("STUCK: lost"), "g")).startswith("STUCK")  # type: ignore[arg-type]
    assert ctx.run.final_shot


@pytest.mark.asyncio
async def test_a_crash_keeps_messages_and_shot_and_reraises() -> None:
    ctx = make_ctx()
    with pytest.raises(RuntimeError, match="model down"):
        await run_goal(ctx, FakeAgent(error=True), "g")  # type: ignore[arg-type]
    assert ctx.run.messages == ["partial"]
    assert ctx.run.final_shot


@pytest.mark.asyncio
async def test_finally_wipes_the_run_values() -> None:
    ctx = make_ctx()

    class Typing(FakeAgent):
        async def ainvoke(self, payload: dict[str, object], config: dict[str, object]) -> object:
            ctx.run.typed_texts.add("74838")
            ctx.run.entered = {"Amount": "55"}
            ctx.run.given.append("Sean")
            return await super().ainvoke(payload, config)

    await run_goal(ctx, Typing(), "g")  # type: ignore[arg-type]
    run = ctx.run
    assert (run.typed_texts, run.entered, run.given, run.look) == (set(), {}, [], None)
    assert {"74838", "55", "sean"} <= run.redact


class HangingAgent(FakeAgent):
    def __init__(self, ctx: Ctx) -> None:
        super().__init__()
        self.ctx = ctx

    async def ainvoke(self, payload: dict[str, object], config: dict[str, object]) -> object:
        self.ctx.run.typed_texts.add("74838")  # a value that must still be wiped
        await asyncio.Event().wait()  # never returns
        raise AssertionError("unreachable")


@pytest.mark.asyncio
async def test_a_run_past_its_deadline_ends_stuck_and_still_wipes() -> None:
    ctx = make_ctx(cfg=DiscoveryConfig(run_timeout_s=0.05))
    answer = await run_goal(ctx, HangingAgent(ctx), "g")  # type: ignore[arg-type]
    run = ctx.run
    assert answer == "STUCK: discovery timed out after 0.05 s"
    assert run.answer == answer
    assert run.stuck == "discovery timed out after 0.05 s"
    assert run.messages == ["partial"]  # what the agent did so far, for the transcript
    assert run.final_shot
    assert run.log[-1]["tool"] == "stuck"
    assert run.log[-1]["args"] == {"reason": "discovery timed out after 0.05 s"}
    assert run.typed_texts == set()  # finally still wiped
    assert "74838" in run.redact


@pytest.mark.asyncio
async def test_a_tools_own_timeout_error_is_not_the_deadline() -> None:
    class ToolTimeout(FakeAgent):
        async def ainvoke(self, payload: dict[str, object], config: dict[str, object]) -> object:
            raise TimeoutError("page.click timed out")

    ctx = make_ctx()
    with pytest.raises(TimeoutError, match="page.click"):
        await run_goal(ctx, ToolTimeout(), "g")  # type: ignore[arg-type]
    assert ctx.run.stuck == ""
    assert ctx.run.final_shot


@pytest.mark.asyncio
async def test_an_outside_cancel_is_not_swallowed_and_still_wipes() -> None:
    ctx = make_ctx()
    task = asyncio.create_task(run_goal(ctx, HangingAgent(ctx), "g"))  # type: ignore[arg-type]
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert ctx.run.stuck == ""
    assert ctx.run.typed_texts == set()


@pytest.mark.asyncio
async def test_evidence_after_a_timed_out_run_says_stuck(tmp_path: Path) -> None:
    ctx = make_ctx(cfg=DiscoveryConfig(run_timeout_s=0.05))
    agent = HangingAgent(ctx)
    agent.aget_state = _state_with(AIMessage("Paying from 74838 now."))  # type: ignore[method-assign]
    await run_goal(ctx, agent, "g")  # type: ignore[arg-type]
    folder = save_evidence(ctx, tmp_path, ocr_fn=lambda i: [])
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["status"] == "STUCK"
    events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
    assert events[-1]["args"]["reason"] == "discovery timed out after 0.05 s"
    assert "74838" not in (folder / "events.jsonl").read_text()
    assert "74838" not in (folder / "transcript.jsonl").read_text()


def _state_with(*messages: object) -> Callable[[dict[str, object]], Awaitable[object]]:
    async def aget_state(config: dict[str, object]) -> object:
        return SimpleNamespace(values={"messages": list(messages)})

    return aget_state

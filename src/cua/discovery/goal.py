"""run_goal: one goal through the discovery agent (moved from discovery.py 1808-1832).

``HANDOFF = HandoffState(goal=goal)`` is ``new_run(ctx, goal)`` (the same ctx, a fresh run); the
``finally`` block is ``wipe(run, secrets)``: values live only for the run. The whole invoke runs
under ``ctx.cfg.run_timeout_s``; past it the run ends STUCK (the same ``mark_stuck`` the step budget
uses), keeps its messages and final shot, and is still wiped. An outside cancel is not swallowed.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Protocol

from cua.discovery.context import Ctx, snap
from cua.discovery.run import wipe
from cua.discovery.tools.guard import log, mark_stuck
from cua.discovery.wiring import new_run


class Agent(Protocol):
    """What run_goal needs of the compiled deep agent."""

    async def ainvoke(self, payload: dict[str, object], config: dict[str, object]) -> object: ...

    async def aget_state(self, config: dict[str, object]) -> object: ...


def _start(ctx: Ctx, goal: str) -> str:
    new_run(ctx, goal)
    log(
        ctx,
        "start",
        {
            "base_url": ctx.site.base_url,
            "viewport": list(ctx.session.cfg.viewport),
            "device_scale_factor": 1,
        },
        "run started",
    )
    return f"discovery-{uuid.uuid4().hex[:8]}"


async def _timed_out(ctx: Ctx, agent: Agent, config: dict[str, object]) -> str:
    """The deadline passed: end the run STUCK, keeping what the agent did so far."""
    reason = f"discovery timed out after {ctx.cfg.run_timeout_s:g} s"
    run = ctx.run
    run.answer = mark_stuck(ctx, reason)
    log(ctx, "stuck", {"reason": reason}, "run timed out")
    run.messages = (await agent.aget_state(config)).values.get("messages", [])  # type: ignore[attr-defined]
    run.final_shot = await snap(ctx)
    return run.answer


async def run_goal(ctx: Ctx, agent: Agent, goal: str, thread_id: str | None = None) -> str:
    """New run on a fresh thread; pass an earlier thread_id to resume it with a next message."""
    if thread_id is None:
        thread_id = _start(ctx, goal)
    print("thread:", thread_id)
    config: dict[str, object] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 4 * ctx.cfg.step_budget,
    }
    run, deadline = ctx.run, asyncio.timeout(ctx.cfg.run_timeout_s)
    try:
        try:
            async with deadline:
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": goal}]}, config=config
                )
        except TimeoutError:
            if not deadline.expired():  # a tool's own timeout, not the run deadline
                raise
            return await _timed_out(ctx, agent, config)
        run.messages = result["messages"]  # type: ignore[index]
        run.answer = run.messages[-1].content  # type: ignore[attr-defined]
        if run.answer.startswith(("STUCK", "DECLINED")):
            run.final_shot = await snap(ctx)
        return run.answer
    except Exception:
        run.messages = (await agent.aget_state(config)).values.get("messages", [])  # type: ignore[attr-defined]
        run.final_shot = await snap(ctx)
        raise
    finally:  # banking: values live only for the run. Keep the log (labels only), drop the rest
        wipe(run, ctx.secrets)

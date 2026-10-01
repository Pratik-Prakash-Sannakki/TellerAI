"""run_goal: one goal through the discovery agent (moved from discovery.py 1808-1832).

``HANDOFF = HandoffState(goal=goal)`` is ``new_run(ctx, goal)`` (the same ctx, a fresh run); the
``finally`` block is ``wipe(run, secrets)``: values live only for the run.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from cua.discovery.context import Ctx, snap
from cua.discovery.run import wipe
from cua.discovery.tools.guard import log
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


async def run_goal(ctx: Ctx, agent: Agent, goal: str, thread_id: str | None = None) -> str:
    """New run on a fresh thread; pass an earlier thread_id to resume it with a next message."""
    if thread_id is None:
        thread_id = _start(ctx, goal)
    print("thread:", thread_id)
    config: dict[str, object] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 4 * ctx.cfg.step_budget,
    }
    run = ctx.run
    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": goal}]}, config=config
        )
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

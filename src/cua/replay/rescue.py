"""R8: the help panel. Take over (the human does this step) or stop.

Moved from notebooks/replay/replay.py 1338-1368 (``rescue``), built from the shared handoff
pieces: ``SiteLock.open()`` (the human's sends still meet both gates), ``handback_button`` (the
toolbar button), ``hand_back`` (panel Done or toolbar click) and ``wait_held_send`` (a send the
human made is gated and released before hand-back). Body otherwise unchanged; globals -> ``ctx``.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import JsonValue

from cua.handoff.extension import handback_button
from cua.handoff.takeover import hand_back, takeover_text, wait_held_send
from cua.replay.context import Ctx
from cua.replay.run import url_path
from cua.replay.wiring import snap
from cua.safety.hosts import host_allowed
from cua.schema import Step, Stop


class Frame(Protocol):
    @property
    def url(self) -> str: ...


async def rescue(ctx: Ctx, i: int, step: Step, why: str) -> dict[str, JsonValue]:
    """Returns the evidence (3.6): screenshots at start and hand-back, page and send paths.
    Never typed values; never new steps."""
    run = ctx.run
    choice = await ctx.control.ask(
        f"Replay needs help at step {i + 1} ({step.action})",
        why,
        "rescue",
        image=run.look.drawn if run.look else None,
    )
    if choice != "takeover":
        raise Stop("STUCK", why)
    start = await snap(ctx)
    acts: dict[str, list[str]] = {"pages": [], "sends": []}
    await _taken_over(ctx, acts)
    ctx.run.human.append({"step": i, "reason": why, "actions": acts})  # type: ignore[dict-item]
    if not await wait_held_send(ctx.guard.lock, ctx.cfg.gate_s):
        raise Stop("STUCK", "the take-over's send is still waiting at the gates")
    if not host_allowed(ctx.page.url, ctx.site):
        raise Stop("FAILED", "the take-over left the allowed site")
    end = await snap(ctx)
    return {"actions": acts, "shots": {"start": start, "end": end}}  # type: ignore[dict-item]


async def _taken_over(ctx: Ctx, acts: dict[str, list[str]]) -> None:
    """The human is in control until Done or the toolbar button; pages they visit are noted."""
    page = ctx.page

    def visited(frame: Frame) -> None:
        if frame is page.main_frame:
            acts["pages"].append(url_path(frame.url))

    ctx.run.takeover = acts
    page.on("framenavigated", visited)  # type: ignore[arg-type]
    try:
        async with ctx.session.lock.open(), handback_button(ctx.session.ext, ctx.bcfg) as button:
            await hand_back(ctx.control, button, takeover_text())
    finally:
        page.remove_listener("framenavigated", visited)  # type: ignore[arg-type]
        ctx.run.takeover = None

"""A dropdown whose value a send carries becomes a step (discovery's send-guard ``on_sent`` hook).

Moved from discovery.py 659-673 (log_sent_dropdowns). The pre-action read itself is
``cua.browser.dropdown.read_dropdowns`` (called by ``context.act``'s prepare hook): this module
never touches the page, because it runs while the send guard holds a request.
"""

from __future__ import annotations

from cua.discovery.context import Ctx, crop
from cua.discovery.recorder.events import is_select, same_spot
from cua.discovery.run import run_values
from cua.discovery.tools.guard import log
from cua.discovery.tools.read_helpers import where
from cua.vision.look import Look


async def log_sent_dropdowns(ctx: Ctx, look: Look, sent: dict[str, str]) -> None:
    """A dropdown whose value this send carries is a step, even one left on its default or set in
    a gate form: replay must choose it, never inherit the page's default. Logged before the send
    click, with its label and position only. The value is never logged, and the crop blanks it."""
    values = {v for v in sent.values() if v}
    for index, d in enumerate(ctx.run.dropdowns):  # read before the click: the page is not touched
        at, box = d["at"], d["box"]
        if at and values & {d["value"], d["text"]}:
            point = (round(at[0] / look.scale), round(at[1] / look.scale))  # type: ignore[index]
            field_box = [round(v / look.scale) for v in box]  # type: ignore[attr-defined]
            here = {"url": look.url, "point": point, "field_box": field_box}
            if any(is_select(ev) and same_spot(ev, here) for ev in ctx.run.log):  # type: ignore[arg-type]
                continue  # the agent already chose this one: never a second step
            spots = where(look, point, run_values(ctx.run, ctx.secrets))
            log(
                ctx,
                "select_option",
                {"hint": spots.get("label") or "option"},
                "sent dropdown",
                point,
                crop(ctx, look, point, None),
                dropdown=True,
                field_box=field_box,
                index=index,
                **spots,
            )

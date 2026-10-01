"""Attach discovery to an open browser session: the send guard on every request, the control
window, the navigation counter. And ``new_run``: a fresh DiscoveryRun for the next goal.

Moved from discovery's setup cell (discovery.py 1074-1084; the lock itself is set by
``open_session``) and the post-approve part of guard_send (836-847) as SendGuard hooks.
Re-run safe: one nav listener per page and one ``cuaReply``/close binding per control tab
(:func:`cua.handoff.binding.bind_control`), each forwarding to the latest attach.

Run swap (design choice): ``Ctx.run`` reads ``guard.state``, so ``new_run`` assigns the guard a
fresh run and returns the same ctx. Tools and the agent built over a ctx never go stale. The
returned ctx is the one passed in; callers may use either.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

from cua.browser.session import Session
from cua.config import DiscoveryConfig
from cua.discovery.context import Ctx
from cua.discovery.run import DiscoveryRun
from cua.discovery.tools.dropdowns import log_sent_dropdowns
from cua.discovery.tools.guard import log
from cua.handoff import discovery_control
from cua.handoff.binding import bind_control
from cua.safety import DISCOVERY_OPTIONS, Request, SendGuard, SendHooks
from cua.safety.send_guard import LookLike
from cua.vision.look import Look

if TYPE_CHECKING:
    from cua.handoff.binding import ControlTab


def _hooks(holder: list[Ctx]) -> SendHooks:
    """Discovery's post-approve steps, in guard_send's order. ``holder`` gets the ctx once built
    (the guard is built before the ctx that holds it)."""

    async def on_sent(
        req: Request, original: dict[str, str], fields: dict[str, str], look: LookLike | None
    ) -> None:
        ctx = holder[0]
        # e.g. a human's $100000: masked in evidence, and never part of a label
        ctx.run.redact |= {v for v in (*original.values(), *fields.values()) if v}
        if look:  # the page's dropdowns hold what was on screen
            await log_sent_dropdowns(ctx, look, original)  # type: ignore[arg-type]
        ctx.run.entered = {}

    def after_verdict(
        req: Request, original: dict[str, str], fields: dict[str, str], human: bool
    ) -> None:
        ctx, path = holder[0], urlparse(req.url).path
        corrected = [k for k in fields if fields[k] != original[k]]
        log(ctx, "send", {"path": path}, "approved by human", corrected=corrected)
        if human and ctx.run.takeover is not None:
            ctx.run.takeover.append({"kind": "send", "path": path})

    return SendHooks(on_sent=on_sent, after_verdict=after_verdict)


def build_ctx(session: Session, cfg: DiscoveryConfig, secrets: Mapping[str, str]) -> Ctx:
    """The ctx with its guard and control window, not yet wired to the page. Call inside the
    running loop (the guard's lock). ``secrets``: secret NAME -> value, from ``.env``."""
    control = discovery_control(session.control_page, session.page)
    holder: list[Ctx] = []
    guard = SendGuard(
        DiscoveryRun(),
        control,
        secrets,
        session.cfg.sensitive_words,
        _hooks(holder),
        DISCOVERY_OPTIONS,
    )
    holder.append(Ctx(session, cfg, guard, control, secrets))
    return holder[0]


def new_run(ctx: Ctx, goal: str) -> Ctx:
    """A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``)."""
    ctx.guard.state = DiscoveryRun(goal=goal)
    return ctx


async def attach(session: Session, cfg: DiscoveryConfig, secrets: Mapping[str, str]) -> Ctx:
    """Route every request through a new send guard, open the control window. Re-run safe: the
    old route is removed first; the nav listener, ``cuaReply`` and the close listener are added
    once per page and forward to the latest ctx / window."""
    ctx = build_ctx(session, cfg, secrets)
    page, control_page = session.page, session.control_page
    await page.unroute("**/*")
    await page.route("**/*", ctx.guard)
    page._cua_ctx = ctx  # type: ignore[attr-defined]  # the one nav listener reads the latest
    if not getattr(page, "_cua_navs", False):  # once per page, even on a re-run
        page.on("framenavigated", lambda f: _count_nav(page, f))
        page._cua_navs = True  # type: ignore[attr-defined]
    # cast: Playwright's overloaded Page.on / wider expose_function can't match ControlTab
    await bind_control(cast("ControlTab", control_page), ctx.control)
    await ctx.control.show("Agent is working")
    await page.bring_to_front()
    print("site locked | control window open")
    return ctx


def _count_nav(page: object, frame: object) -> None:
    """Counts on the ctx of the latest attach to this page."""
    ctx: Ctx = page._cua_ctx  # type: ignore[attr-defined]
    ctx.run.navs += frame == ctx.page.main_frame


__all__ = ["Look", "attach", "build_ctx", "new_run"]

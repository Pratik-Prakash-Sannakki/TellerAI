"""Ctx: what every discovery tool is given, plus the page wrappers the tools share.

``Ctx`` replaces the notebook's globals (``page``, ``CONTROL``, ``CFG``, ``HANDOFF``, ``SECRETS``,
``SEND_GATE``). ``ctx.run`` is not a field: it is whatever run the send guard currently serves
(``guard.state``), so ``wiring.new_run`` swaps ONE object and tools built once over this ctx (and
the agent built from them) always see the current run. Nothing is hidden at module level.

The wrappers are the notebook's own page helpers with ``ctx`` first: ``look`` (take_look,
discovery.py 238-252), ``canvas``/``to_page`` (269-279), ``snap`` (521-527), ``act`` (973-985),
``into_box`` (988-991), ``list_options``/``choose_option`` (1020-1035), ``dropdown_under`` (is a
native <select> right under a point), and ``crop`` (cut_crop at the current canvas size).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from playwright.async_api import Page

from cua.browser import input as browser_input
from cua.browser.dropdown import (
    DROPDOWNS_WITH_BOX_JS,
    choose_option_at_point,
    read_dropdowns,
    select_under,
)
from cua.browser.dropdown import (
    list_options as page_options,
)
from cua.browser.input import Step, wait_for_change
from cua.browser.session import Session
from cua.config import DiscoveryConfig, SiteProfile
from cua.discovery.run import DiscoveryRun, run_values
from cua.discovery.tools.read_helpers import page_texts
from cua.handoff import ControlWindow
from cua.safety import SendGuard, hide_secrets, norm
from cua.vision.canvas import canvas_size
from cua.vision.canvas import to_page as canvas_to_page
from cua.vision.crops import cut_crop, read_near
from cua.vision.look import Element, Look
from cua.vision.screenshot import snap_png, take_look


@dataclass(frozen=True)
class Ctx:
    session: Session  # the browser: site tab, control tab, extension, site lock, refs
    cfg: DiscoveryConfig
    guard: SendGuard  # the route handler; ``guard.lock`` is the send gate
    control: ControlWindow  # discovery's "Agent control" tab
    secrets: Mapping[str, str]  # secret NAME -> value, in memory only (from .env)

    @property
    def run(self) -> DiscoveryRun:
        """The current run (the one the send guard serves)."""
        return cast("DiscoveryRun", self.guard.state)

    @property
    def site(self) -> SiteProfile:
        return self.session.site

    @property
    def page(self) -> Page:
        return self.session.page


def _count_start(ctx: Ctx, lk: Look) -> None:
    """The start event's look bookkeeping: the page a run begins on, and how often each text is
    seen (text on most looks is chrome)."""
    start = cast("dict[str, Any]", ctx.run.log[0] if ctx.run.log else {})
    if start.get("tool") == "start":
        texts = page_texts(lk, run_values(ctx.run, ctx.secrets))
        start.setdefault("start_texts", texts)
        start["looks"] = start.get("looks", 0) + 1
        counts = start.setdefault("text_counts", {})
        for t in {norm(t) for t in texts}:
            counts[t] = counts.get(t, 0) + 1


async def look(ctx: Ctx) -> Look:
    """The only screenshot path; stores the look on the run."""

    def on_look(lk: Look) -> None:
        ctx.run.look = lk
        _count_start(ctx, lk)

    s = ctx.session
    return await take_look(s.page, s.cfg, s.refs, on_look)


def canvas(ctx: Ctx) -> tuple[int, int]:
    """The size of the image the model is looking at right now."""
    return canvas_size(ctx.run.look, ctx.session.cfg.viewport)


def to_page(ctx: Ctx, point: tuple[int, int]) -> tuple[float, float]:
    return canvas_to_page(ctx.run.look, point)


def crop(ctx: Ctx, lk: Look, point: tuple[int, int], keep: Element | None) -> bytes:
    """Crop around the target, every other text blanked (sized to the current canvas)."""
    return cut_crop(lk, point, keep, canvas(ctx), ctx.session.cfg)


async def snap(ctx: Ctx) -> bytes | None:
    """An evidence screenshot: short timeout, None on failure (never hangs on a held send)."""
    return await snap_png(ctx.page, ctx.cfg.snap_ms)


async def act(ctx: Ctx, *steps: Step) -> Look:
    """Unlock the site tab, run our own input steps, relock, settle, take a new look."""

    async def prepare() -> None:  # what a send from this action will need
        ctx.run.dropdowns = await read_dropdowns(
            ctx.page, DROPDOWNS_WITH_BOX_JS, ctx.cfg.snap_ms / 1000
        )

    async def settled(before: bytes) -> None:
        if ctx.run.verdict.startswith("SENT"):
            await wait_for_change(ctx.page, before, ctx.cfg.send_wait_ms, ctx.session.cfg)

    return await browser_input.act(
        ctx.session,
        steps,
        send_gate=ctx.guard.lock,
        look_fn=lambda: look(ctx),
        prepare=prepare,
        settled=settled,
    )


def into_box(ctx: Ctx, point: tuple[int, int], value: str) -> tuple[Step, Step, Step, Step, Step]:
    """Focus the site tab, click the box, clear it, type (see ``browser.input.into_box``)."""
    return browser_input.into_box(ctx.page, ctx.run.look, point, value)


async def list_options(ctx: Ctx, point: tuple[int, int]) -> list[str]:
    """Every option of the dropdown at this point ([] if it is not a dropdown)."""
    return await page_options(ctx.page, to_page(ctx, point), lambda t: hide_secrets(t, ctx.secrets))


async def dropdown_under(ctx: Ctx, point: tuple[int, int]) -> int | None:
    """The index of the native <select> right under this point, or None (bounded; None on error)."""
    return await select_under(ctx.page, to_page(ctx, point), ctx.cfg.snap_ms / 1000)


async def choose_option(ctx: Ctx, point: tuple[int, int], option: str) -> int | None:
    """Select the first option containing this text in the dropdown at (or next to) this point;
    OCR of the dropdown's own box confirms it. Its index among the page's <select>s, or None."""

    def shown(lk: Look, at: tuple[int, int], want: str) -> bool:
        return norm(want) in norm(read_near(lk, at, canvas(ctx), ctx.session.cfg))

    return await choose_option_at_point(
        ctx.session, to_page(ctx, point), option, look_fn=lambda: look(ctx), confirm=shown
    )

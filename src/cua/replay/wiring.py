"""Page wiring for replay: :func:`attach` (the notebook's setup cell, replay.py 709-726) and the
thin page wrappers every step uses -- :func:`look`, :func:`canvas`, :func:`to_page`, :func:`snap`,
:func:`act`, :func:`stash_dropdowns`, :func:`note_response`.

Globals become ``ctx`` (see :mod:`cua.replay.context`). The setup is the notebook's, in order:
route every request through the send guard (``unroute`` first, so a re-run never stacks two), a
response listener once per page (network metadata only), the replay control window with
``cuaReply`` exposed (tolerating "already registered" on a re-run), the control tab's close ->
``on_reply(None)`` (fail closed), "Replay is working", and the site tab back to front. The site
lock is already set by ``open_session``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from cua.browser import input as browser_input
from cua.browser.dropdown import DROPDOWNS_JS, read_dropdowns
from cua.browser.session import Session
from cua.config import ReplayConfig, SiteProfile, secret_values  # noqa: F401  re-export (D config)
from cua.handoff.control_window import replay_control
from cua.replay.context import Ctx
from cua.replay.run import url_path
from cua.vision import Look, canvas_size
from cua.vision import to_page as page_point
from cua.vision.screenshot import snap_look, take_look

Step = Callable[[], Awaitable[None]]


class _Request(Protocol):
    def is_navigation_request(self) -> bool: ...


class Response(Protocol):
    """The Playwright ``Response`` fields note_response reads."""

    @property
    def request(self) -> _Request: ...

    @property
    def frame(self) -> object: ...

    @property
    def status(self) -> int: ...

    @property
    def url(self) -> str: ...


async def attach(session: Session, site: SiteProfile, cfg: ReplayConfig) -> Ctx:
    """Wire replay onto an open session and return its Ctx."""
    page, control_page = session.page, session.control_page
    control = replay_control(control_page, page)

    async def shoot() -> Look:
        return await take_look(page, session.cfg, session.refs)

    ctx = Ctx(session, cfg, control, secret_values(site), shoot)
    await page.unroute("**/*")
    await page.route("**/*", ctx.guard)  # type: ignore[arg-type]
    if not getattr(page, "_cua_responses", False):  # once per page, even on a re-run
        page.on("response", lambda r: note_response(ctx, r))  # type: ignore[arg-type]
        page._cua_responses = True  # type: ignore[attr-defined]
    await _expose(ctx)
    await control.show("Replay is working")
    if not page.is_closed():
        await page.bring_to_front()
    return ctx


async def _expose(ctx: Ctx) -> None:
    control_page = ctx.session.control_page
    try:
        await control_page.expose_function("cuaReply", ctx.control.on_reply)
    except Exception as e:
        if "already registered" not in str(e):
            raise
    control_page.on("close", lambda _: ctx.control.on_reply(None))


def note_response(ctx: Ctx, resp: Response) -> None:
    """Keep the main document's HTTP status (not sub-resources, not iframes)."""
    if resp.request.is_navigation_request() and resp.frame is ctx.page.main_frame:
        ctx.run.http, ctx.run.navs = (resp.status, url_path(resp.url)), ctx.run.navs + 1


async def look(ctx: Ctx) -> Look:
    """The only screenshot path; the look is stored on the run (the notebook's take_look)."""
    ctx.run.look = await ctx.shoot()
    return ctx.run.look


def canvas(ctx: Ctx) -> tuple[int, int]:
    return canvas_size(ctx.run.look, ctx.bcfg.viewport)


def to_page(ctx: Ctx, point: tuple[int, int]) -> tuple[float, float]:
    return page_point(ctx.run.look, point)


async def snap(ctx: Ctx) -> bytes | None:
    """Evidence screenshot. A held form POST blocks `page.screenshot()`: give up, never crash."""
    return await snap_look(lambda: look(ctx), ctx.cfg.snap_s)


async def act(ctx: Ctx, *steps: Step) -> Look:
    """Unlock the site tab, run our own input steps, relock, settle, take a new look."""
    return await browser_input.act(
        ctx.session, steps, send_gate=ctx.guard.lock, look_fn=lambda: look(ctx)
    )


async def stash_dropdowns(ctx: Ctx) -> list[dict[str, object]]:
    """Before a click: a held send blocks `page.evaluate`, so the guard only reads this stash."""
    ctx.run.dropdowns = await read_dropdowns(ctx.page, DROPDOWNS_JS, ctx.cfg.page_s)
    return ctx.run.dropdowns

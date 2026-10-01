"""Our own input into the locked site tab: ``act`` (unlock, run steps, relock, settle, look),
``into_box`` (click, clear, type) and ``wait_for_change`` (wait for a send's response).

Moved from discovery.py 961-990 and replay.py 632-646. The two ``act``s differ only in
discovery's extras, which are now explicit hooks so each side keeps its exact call order:

- replay: ``act(session, steps, send_gate=..., look_fn=...)``:
  unlock -> steps -> relock -> settle -> send gate -> look.
- discovery: also ``prepare`` (its ``read_dropdowns`` into HANDOFF) and ``settled`` (its "if the
  verdict is SENT, wait_for_change(before)"): screenshot ``before`` -> prepare -> unlock -> steps
  -> relock -> settle -> send gate -> settled(before) -> look. ``before`` is taken only when
  ``settled`` is given (replay never took one).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence

from playwright.async_api import Page

from cua.browser.session import Session
from cua.config import BrowserConfig
from cua.vision.canvas import to_page
from cua.vision.crops import screens_same
from cua.vision.look import Look

Step = Callable[[], Awaitable[None]]


async def wait_for_change(page: Page, before: bytes, send_wait_ms: int, cfg: BrowserConfig) -> None:
    """The response to a send lands after the human's approval, not after the click: wait until
    the page differs from before the click and has stopped changing (bounded)."""
    end, last = time.monotonic() + send_wait_ms / 1000, before
    while time.monotonic() < end:
        await page.wait_for_timeout(cfg.settle_ms)
        shot = await page.screenshot()
        if not screens_same(before, shot, cfg) and screens_same(last, shot, cfg):
            return
        last = shot


async def act(  # noqa: PLR0913 (constraints allow 6)
    session: Session,
    steps: Sequence[Step],
    *,
    send_gate: asyncio.Lock,
    look_fn: Callable[[], Awaitable[Look]],
    prepare: Callable[[], Awaitable[None]] | None = None,
    settled: Callable[[bytes], Awaitable[None]] | None = None,
) -> Look:
    """Unlock the site tab, run our own input steps, relock, settle, take a new look."""
    page = session.page
    before = await page.screenshot() if settled is not None else b""
    if prepare is not None:
        await prepare()  # discovery: what a send from this action will need
    async with session.lock.open():
        for step in steps:
            await step()
    await page.wait_for_timeout(session.cfg.settle_ms)
    async with send_gate:  # a send held for the human finishes first
        pass
    if settled is not None:
        await settled(before)
    return await look_fn()


def into_box(
    page: Page, look: Look | None, point: tuple[int, int], value: str
) -> tuple[Step, Step, Step, Step]:
    """Click the box, clear what is in it, type. Retries replace instead of doubling up."""
    return (
        lambda: page.mouse.click(*to_page(look, point)),
        lambda: page.keyboard.press("ControlOrMeta+A"),
        lambda: page.keyboard.press("Backspace"),
        lambda: page.keyboard.type(value),
    )

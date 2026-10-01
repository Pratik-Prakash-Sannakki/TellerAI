"""The hand-back extension (the Chrome toolbar button): its service worker, never the site page.

Moved from discovery.py 576-597 and replay.py 1290-1324. ``ext_call`` is identical on both sides
apart from the order of the except tuple. ``button_clicked``/``handback_button`` are replay's;
discovery's ``watch_button`` is ``button_clicked`` followed by ``control.answer("takeover",
"done")`` (same base read and poll loop). The ``EXT``/``CFG``/``CONTROL`` globals are parameters.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Protocol

from playwright.async_api import Error as PlaywrightError

from cua.config import BrowserConfig

CLICKS = "self.handbackClicked || 0"


class Extension(Protocol):
    """The extension's service worker (a Playwright ``Worker``)."""

    async def evaluate(self, expression: str) -> object: ...


class Answerable(Protocol):
    def answer(self, mode: str, value: str) -> None: ...


async def ext_call(ext: Extension | None, script: str, timeout_s: float) -> object:
    """Q16/R19: one bounded call into the hand-back extension's service worker, never the site
    page. No extension, or one that errors or hangs, gives None: the take-over carries on."""
    if ext is None:
        return None
    try:
        return await asyncio.wait_for(ext.evaluate(script), timeout_s)
    except (TimeoutError, PlaywrightError):
        return None


async def button_clicked(ext: Extension | None, poll_s: float, timeout_s: float) -> None:
    """Returns once the toolbar button's click count rises above where it was at the start."""
    base = await ext_call(ext, CLICKS, timeout_s)
    while True:
        await asyncio.sleep(poll_s)
        n = await ext_call(ext, CLICKS, timeout_s)
        if base is None:
            base = n
        elif n is not None and n > base:  # type: ignore[operator]
            return


async def watch_button(ext: Extension | None, cfg: BrowserConfig, control: Answerable) -> None:
    """Discovery: hands back once the toolbar button's click count rises above the start."""
    await button_clicked(ext, cfg.ext_poll_s, cfg.ext_s)
    control.answer("takeover", "done")


@contextlib.asynccontextmanager
async def handback_button(
    ext: Extension | None, cfg: BrowserConfig
) -> AsyncIterator[asyncio.Future[None]]:
    """Badge YOU while the human is in control; yields the task a toolbar click completes."""
    await ext_call(ext, "setMode('YOU')", cfg.ext_s)
    clicked = asyncio.ensure_future(button_clicked(ext, cfg.ext_poll_s, cfg.ext_s))
    try:
        yield clicked
    finally:
        clicked.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await clicked
        await ext_call(ext, "setMode('AI')", cfg.ext_s)

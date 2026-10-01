"""The only screenshot path: page screenshot -> canvas -> OCR -> numbered :class:`Look`.

Moved from discovery.py 238-252 (``take_look``) / replay.py 235-240 (the common body), 264-266
(``page_width``), discovery.py 521-527 (``snap`` -> :func:`snap_png`) and replay.py 1277-1282
(``snap`` -> :func:`snap_look`). Changes: globals become parameters; discovery's start-log
bookkeeping is the caller's ``on_look`` hook; callers store the look themselves; and (decision 3)
the CPU-bound part -- decode, to_canvas, OCR + numbering, drawing, encoding -- runs in one
``asyncio.to_thread`` call so page calls stay on the event loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from cua.config import BrowserConfig
from cua.vision.canvas import to_canvas
from cua.vision.look import Look, decode, encode
from cua.vision.ocr import RefCounter, draw_numbered, number, ocr


async def page_width(page: Page) -> int:
    """The window's width in mouse points (the browser's size, not the site's content)."""
    return int(await page.evaluate("window.innerWidth"))


def _build_look(png: bytes, points_w: int, url: str, cfg: BrowserConfig, refs: RefCounter) -> Look:
    """The CPU-bound half of take_look (run in a worker thread)."""
    img, scale = to_canvas(decode(png), points_w, cfg.viewport)
    elements = number(ocr(img, cfg.ocr_min_score), refs)
    return Look(encode(img), draw_numbered(img, elements), elements, url, scale)


async def take_look(
    page: Page,
    cfg: BrowserConfig,
    refs: RefCounter,
    on_look: Callable[[Look], None] | None = None,
) -> Look:
    """The only screenshot path. The page is fixed (Q10), so this is normally 1:1; the rescale is
    only a safety net if a screenshot ever comes back at another pixel density."""
    png, points_w = await page.screenshot(), await page_width(page)
    look = await asyncio.to_thread(_build_look, png, points_w, page.url, cfg, refs)
    if on_look is not None:
        on_look(look)
    return look


async def snap_png(page: Page, timeout_ms: int) -> bytes | None:
    """An evidence screenshot: short timeout, None on failure. A page whose navigation is held by
    guard_send never finishes a screenshot, so evidence must never be able to hang or crash a run.
    (Discovery's ``snap``.)"""
    try:
        return await page.screenshot(timeout=timeout_ms, animations="disabled")
    except PlaywrightError:
        return None


async def snap_look(look_fn: Callable[[], Awaitable[Look]], timeout_s: float) -> bytes | None:
    """Evidence screenshot. A held form POST blocks ``page.screenshot()``: give up, never crash.
    (Replay's ``snap``; ``look_fn`` is replay's own take_look, which also stores the look.)"""
    try:
        return (await asyncio.wait_for(look_fn(), timeout_s)).png
    except (TimeoutError, PlaywrightError):
        return None

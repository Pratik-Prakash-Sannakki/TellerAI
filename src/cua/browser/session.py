"""Session: the open browser (Playwright, context, site tab, control tab, hand-back extension, site
lock, element refs), and ``open_session`` that launches it.

Moved from the setup cells of discovery.py 117-139 and replay.py 116-137 (identical apart from the
temp-dir prefix, now ``profile_prefix``). Reuse follows replay's rule (the superset): a given
``existing`` session whose site and control pages are both still open is returned unchanged, so a
notebook re-run never leaks a browser. The ``CDP`` session -> :class:`SiteLock` and
``await lock.set(True)`` come from the locking cells (discovery.py 1074-1075 / replay.py 709-710).
The route/guard_send, control window and ``goto`` stay with their later owners (safety/handoff/
run). The viewport refusal (discovery.py 136-138) is :func:`check_viewport`, run after ``goto``.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import BrowserContext, Page, Playwright, Worker, async_playwright
from playwright.async_api import Error as PlaywrightError

from cua.browser.site_lock import SiteLock
from cua.config import BrowserConfig, SiteProfile
from cua.vision.look import decode
from cua.vision.ocr import RefCounter


@dataclass(frozen=True)
class Session:
    pw: Playwright
    context: BrowserContext
    page: Page  # the site tab
    control_page: Page  # our own "Agent control" tab
    ext: Worker | None  # the hand-back extension's service worker, None if it did not load
    cfg: BrowserConfig
    site: SiteProfile
    lock: SiteLock
    refs: RefCounter


def handback_dir(start: Path) -> Path:
    """The hand-back extension (Q16), found by walking up from ``start``."""
    return next(
        p / "extensions/handback"
        for p in (start, *start.parents)
        if (p / "extensions/handback/manifest.json").is_file()
    )


def _alive(existing: Session | None) -> bool:
    return existing is not None and not any(
        p.is_closed() for p in (existing.page, existing.control_page)
    )


async def _launch(pw: Playwright, cfg: BrowserConfig, profile_prefix: str) -> BrowserContext:
    w, h = cfg.viewport
    ext_dir = handback_dir(Path.cwd())
    return await pw.chromium.launch_persistent_context(
        tempfile.mkdtemp(prefix=profile_prefix),
        headless=False,
        viewport={"width": w, "height": h},
        device_scale_factor=1,
        args=[
            f"--window-size={w},{h + 140}",
            f"--disable-extensions-except={ext_dir}",
            f"--load-extension={ext_dir}",
        ],
    )


async def close_session(session: Session) -> None:
    """Close the browser window and stop Playwright. The notebooks keep it open between runs on
    purpose (re-running a cell reuses it), so they call this from their own Close cell."""
    await session.context.close()
    await session.pw.stop()


async def _extension(context: BrowserContext) -> Worker | None:
    try:
        return (
            context.service_workers[0]
            if context.service_workers
            else await context.wait_for_event("serviceworker", timeout=5000)
        )
    except PlaywrightError:
        return None  # the take-over still hands back from the control tab


async def open_session(
    site: SiteProfile,
    cfg: BrowserConfig,
    *,
    existing: Session | None = None,
    profile_prefix: str = "cua-",
) -> Session:
    """One visible Chromium at a fixed page size and zoom (Q10), the site tab plus our control tab,
    with the hand-back extension loaded and the site tab locked."""
    if existing is not None and _alive(existing):
        return existing
    pw = existing.pw if existing is not None else await async_playwright().start()
    context = await _launch(pw, cfg, profile_prefix)
    page = context.pages[0] if context.pages else await context.new_page()
    control_page = await context.new_page()
    ext = await _extension(context)
    print("hand-back extension:", "loaded" if ext else "NOT loaded")
    lock = SiteLock(await page.context.new_cdp_session(page))
    await lock.set(True)
    return Session(pw, context, page, control_page, ext, cfg, site, lock, RefCounter())


async def check_viewport(session: Session) -> None:
    """Q10: refuse rather than record a mismatch between the screenshot and the configured page."""
    shot = decode(await session.page.screenshot())
    if (shot.shape[1], shot.shape[0]) != session.cfg.viewport:
        raise RuntimeError(
            f"screenshot is {shot.shape[1]}x{shot.shape[0]}, expected {session.cfg.viewport}"
        )

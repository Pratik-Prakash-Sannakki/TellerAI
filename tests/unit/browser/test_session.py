"""open_session reuses a live session (a notebook re-run must not leak a browser), finds the
hand-back extension by walking up from cwd, and check_viewport refuses a mismatched screenshot."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import cv2
import numpy as np
import pytest

from cua.browser import session as session_mod
from cua.browser.session import Session, check_viewport, handback_dir, open_session
from cua.browser.site_lock import SiteLock
from cua.config import BrowserConfig, load_site
from cua.vision.ocr import RefCounter


class LivePage:
    def __init__(self, closed: bool = False, png: bytes = b"") -> None:
        self.closed, self.png = closed, png

    def is_closed(self) -> bool:
        return self.closed

    async def screenshot(self) -> bytes:
        return self.png


def _session(page: LivePage, control: LivePage, cfg: BrowserConfig | None = None) -> Session:
    return Session(
        pw=cast("object", None),  # type: ignore[arg-type]
        context=cast("object", None),  # type: ignore[arg-type]
        page=page,  # type: ignore[arg-type]
        control_page=control,  # type: ignore[arg-type]
        ext=None,
        cfg=cfg or BrowserConfig(),
        site=load_site("parabank"),
        lock=cast(SiteLock, None),
        refs=RefCounter(),
    )


@pytest.mark.asyncio
async def test_a_live_existing_session_is_returned_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_playwright() -> None:
        raise AssertionError("playwright must not be touched")

    monkeypatch.setattr(session_mod, "async_playwright", no_playwright)
    live = _session(LivePage(), LivePage())
    got = await open_session(live.site, live.cfg, existing=live)
    assert got is live


def test_handback_dir_walks_up_from_the_start(tmp_path: Path) -> None:
    ext = tmp_path / "extensions/handback"
    ext.mkdir(parents=True)
    (ext / "manifest.json").write_text("{}")
    deep = tmp_path / "a/b"
    deep.mkdir(parents=True)
    assert handback_dir(deep) == ext


def _png(w: int, h: int) -> bytes:
    return cv2.imencode(".png", np.zeros((h, w, 3), np.uint8))[1].tobytes()


@pytest.mark.asyncio
async def test_check_viewport_accepts_the_configured_size() -> None:
    cfg = BrowserConfig(viewport=(40, 20))
    await check_viewport(_session(LivePage(png=_png(40, 20)), LivePage(), cfg))


@pytest.mark.asyncio
async def test_check_viewport_refuses_another_size() -> None:
    cfg = BrowserConfig(viewport=(40, 20))
    with pytest.raises(RuntimeError, match="screenshot is 30x20, expected"):
        await check_viewport(_session(LivePage(png=_png(30, 20)), LivePage(), cfg))


@pytest.mark.asyncio
async def test_close_session_deletes_the_browser_profile(tmp_path: Path) -> None:
    """The profile (cookies, cache, history of a bank session) was left in /tmp after close."""
    profile = tmp_path / "cua-profile"
    (profile / "Default").mkdir(parents=True)
    (profile / "Default" / "Cookies").write_text("session")
    closed: list[str] = []

    class Closer:
        async def close(self) -> None:
            closed.append("context")

        async def stop(self) -> None:
            closed.append("pw")

    s = _session(LivePage(), LivePage())
    s = Session(**{**s.__dict__, "pw": Closer(), "context": Closer(), "profile": profile})  # type: ignore[arg-type]
    await session_mod.close_session(s)
    assert closed == ["context", "pw"]
    assert not profile.exists()


@pytest.mark.asyncio
async def test_a_session_without_a_profile_closes_too() -> None:
    class Closer:
        async def close(self) -> None: ...

        async def stop(self) -> None: ...

    s = _session(LivePage(), LivePage())
    await session_mod.close_session(Session(**{**s.__dict__, "pw": Closer(), "context": Closer()}))  # type: ignore[arg-type]

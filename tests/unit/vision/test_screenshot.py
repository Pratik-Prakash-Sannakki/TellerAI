"""take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one worker thread,
then the caller's on_look hook. snap_png/snap_look never crash or hang a run."""

from __future__ import annotations

import asyncio
import threading

import cv2
import numpy as np
import pytest
from playwright.async_api import Error as PlaywrightError

from cua.config import BrowserConfig
from cua.vision import screenshot
from cua.vision.look import Box, Look
from cua.vision.ocr import RefCounter


class ShotPage:
    url = "https://example.test/p"

    def __init__(self, png: bytes, width: int, fail: bool = False) -> None:
        self.png, self.width, self.fail = png, width, fail
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def screenshot(self, **kwargs: object) -> bytes:
        self.calls.append(("screenshot", kwargs))
        if self.fail:
            raise PlaywrightError("held")
        return self.png

    async def evaluate(self, js: str) -> int:
        self.calls.append(("evaluate", {"js": js}))
        return self.width


def _png(w: int, h: int) -> bytes:
    return cv2.imencode(".png", np.zeros((h, w, 3), np.uint8))[1].tobytes()


@pytest.mark.asyncio
async def test_take_look_runs_ocr_in_a_thread_and_calls_on_look(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    threads: list[int] = []

    def fake_ocr(img: object, min_score: float) -> list[tuple[str, Box]]:
        threads.append(threading.get_ident())
        return [("Log In", Box(1, 1, 10, 10))]

    monkeypatch.setattr(screenshot, "ocr", fake_ocr)
    seen: list[Look] = []
    page = ShotPage(_png(40, 20), width=80)
    cfg = BrowserConfig(viewport=(40, 20))
    look = await screenshot.take_look(page, cfg, RefCounter(), seen.append)  # type: ignore[arg-type]
    assert threads
    assert threads[0] != threading.get_ident()
    assert seen == [look]
    assert [(e.ref, e.text) for e in look.elements] == [(1, "Log In")]
    assert look.url == "https://example.test/p"
    assert look.scale == page.width / cfg.viewport[0]
    assert [c[0] for c in page.calls] == ["screenshot", "evaluate"]


@pytest.mark.asyncio
async def test_page_width_reads_the_window_width() -> None:
    page = ShotPage(b"", width=1280)
    assert await screenshot.page_width(page) == page.width  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_snap_png_passes_the_timeout_and_gives_none_on_error() -> None:
    page = ShotPage(b"png", width=1)
    assert await screenshot.snap_png(page, 3000) == b"png"  # type: ignore[arg-type]
    assert page.calls[0] == ("screenshot", {"timeout": 3000, "animations": "disabled"})
    assert await screenshot.snap_png(ShotPage(b"", 1, fail=True), 3000) is None  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_snap_look_gives_the_look_png_or_none_on_timeout() -> None:
    async def quick() -> Look:
        return Look(b"p", b"d", (), "u")

    async def stuck() -> Look:
        await asyncio.sleep(10)
        raise AssertionError

    assert await screenshot.snap_look(quick, 1.0) == b"p"
    assert await screenshot.snap_look(stuck, 0.01) is None

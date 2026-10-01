"""The hand-back extension's toolbar button: its service worker only, never the site page.

Pins the pieces of tests/discovery/test_handback.py and tests/replay/test_handback_button.py that
cover ext_call / the button poll / the badge. The take_over and rescue bodies those files drive
stay with their side (steps 8/9), so those old files keep running against the notebooks.
"""

from __future__ import annotations

import asyncio

import pytest
from playwright.async_api import Error as PlaywrightError

from cua.config import BrowserConfig
from cua.handoff.extension import button_clicked, ext_call, handback_button, watch_button

CFG = BrowserConfig(ext_s=0.05, ext_poll_s=0.01)


class Ext:
    """The extension's service worker: a click counter and a badge."""

    def __init__(self, clicks: int = 0, hang: bool = False, fail: bool = False) -> None:
        self.clicks, self.calls, self.hang, self.fail = clicks, list[str](), hang, fail

    async def evaluate(self, script: str) -> object:
        self.calls.append(script)
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise PlaywrightError("Target closed")
        return self.clicks if "handbackClicked" in script else None

    @property
    def modes(self) -> list[str]:
        return [c for c in self.calls if c.startswith("setMode")]


class Control:
    def __init__(self) -> None:
        self.answered: list[tuple[str, str]] = []

    def answer(self, mode: str, value: str) -> None:
        self.answered.append((mode, value))


@pytest.mark.parametrize("ext", [None, Ext(fail=True), Ext(hang=True)])
@pytest.mark.asyncio
async def test_a_missing_or_broken_extension_gives_none(ext: Ext | None) -> None:
    assert await ext_call(ext, "self.handbackClicked || 0", 0.05) is None


@pytest.mark.asyncio
async def test_ext_call_returns_the_workers_value() -> None:
    clicks = 2
    assert await ext_call(Ext(clicks=clicks), "self.handbackClicked || 0", 0.05) == clicks


@pytest.mark.asyncio
async def test_a_click_count_rise_returns() -> None:
    ext = Ext(clicks=3)  # 3 = an earlier take-over's clicks: the baseline
    task = asyncio.create_task(button_clicked(ext, CFG.ext_poll_s, CFG.ext_s))
    await asyncio.sleep(0.05)
    assert not task.done()
    ext.clicks += 1
    await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_no_base_read_takes_the_first_poll_as_the_base() -> None:
    ext = Ext(clicks=5, fail=True)  # the first read fails: base is None
    task = asyncio.create_task(button_clicked(ext, CFG.ext_poll_s, CFG.ext_s))
    await asyncio.sleep(0.03)
    ext.fail = False  # next poll reads 5 -> base, not a click
    await asyncio.sleep(0.05)
    assert not task.done()
    ext.clicks += 1
    await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_the_badge_reads_you_then_ai_and_the_poll_is_cancelled() -> None:
    ext = Ext()
    before = asyncio.all_tasks()
    async with handback_button(ext, CFG) as clicked:
        assert ext.modes == ["setMode('YOU')"]
        assert not clicked.done()
    polls = len(ext.calls)
    await asyncio.sleep(0.05)
    assert ext.modes == ["setMode('YOU')", "setMode('AI')"]
    assert asyncio.all_tasks() == before
    assert len(ext.calls) == polls
    assert clicked.cancelled()


@pytest.mark.asyncio
async def test_the_badge_resets_even_when_the_body_fails() -> None:
    ext = Ext()
    with pytest.raises(RuntimeError):
        async with handback_button(ext, CFG):
            raise RuntimeError("boom")
    assert ext.modes[-1] == "setMode('AI')"


@pytest.mark.asyncio
async def test_handback_button_yields_a_task_a_click_completes() -> None:
    ext = Ext(clicks=1)
    async with handback_button(ext, CFG) as clicked:
        await asyncio.sleep(0.03)
        ext.clicks += 1
        await asyncio.wait_for(clicked, 1)


@pytest.mark.asyncio
async def test_watch_button_answers_the_takeover_on_a_click() -> None:
    ext, control = Ext(clicks=4), Control()
    task = asyncio.create_task(watch_button(ext, CFG, control))
    await asyncio.sleep(0.05)
    assert control.answered == []
    ext.clicks += 1
    await asyncio.wait_for(task, 1)
    assert control.answered == [("takeover", "done")]

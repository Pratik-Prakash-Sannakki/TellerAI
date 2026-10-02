"""act/into_box/wait_for_change: our own input runs only inside the unlocked site tab, a held send
finishes first, and each side's extra hooks run in that side's old order."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import cast

import cv2
import numpy as np
import pytest

from cua.browser.input import act, into_box, wait_for_change
from cua.browser.session import Session
from cua.config import BrowserConfig
from cua.vision.look import Look


class FakeBox:
    """A text box: Ctrl/Cmd+A then Backspace clears it; type appends."""

    def __init__(self) -> None:
        self.value, self.selected = "", False
        self.mouse, self.keyboard = self, self

    async def click(self, *_: float) -> None:
        self.selected = False

    async def bring_to_front(self) -> None:
        pass

    async def press(self, key: str) -> None:
        if key == "ControlOrMeta+A":
            self.selected = True
        elif key == "Backspace" and self.selected:
            self.value, self.selected = "", False

    async def type(self, text: str) -> None:
        self.value += text


@pytest.mark.asyncio
async def test_typing_twice_does_not_double() -> None:
    page = FakeBox()
    for _ in range(2):
        for step in into_box(page, None, (10, 10), "Pratik"):  # type: ignore[arg-type]
            await step()
    assert page.value == "Pratik"


@pytest.mark.asyncio
async def test_into_box_clicks_at_the_page_point_of_the_look() -> None:
    clicks: list[tuple[float, ...]] = []
    page = FakeBox()

    async def click(*p: float) -> None:
        clicks.append(p)

    page.click = click  # type: ignore[method-assign]
    await into_box(page, Look(b"", b"", (), "u", 2.0), (10, 5), "x")[1]()  # type: ignore[arg-type]  # [0] focuses
    assert clicks == [(20.0, 10.0)]


@dataclass
class Trace:
    log: list[str] = field(default_factory=list)


class TracePage:
    def __init__(self, trace: Trace) -> None:
        self.t = trace

    async def screenshot(self) -> bytes:
        self.t.log.append("screenshot")
        return b"before"

    async def wait_for_timeout(self, ms: int) -> None:
        self.t.log.append(f"wait {ms}")


class TraceLock:
    def __init__(self, trace: Trace) -> None:
        self.t = trace

    @contextlib.asynccontextmanager
    async def open(self) -> AsyncIterator[None]:
        self.t.log.append("unlock")
        try:
            yield
        finally:
            self.t.log.append("lock")


def _session(trace: Trace) -> Session:
    return Session(
        pw=None,  # type: ignore[arg-type]
        context=None,  # type: ignore[arg-type]
        page=TracePage(trace),  # type: ignore[arg-type]
        control_page=None,  # type: ignore[arg-type]
        ext=None,
        cfg=BrowserConfig(settle_ms=7),
        site=None,  # type: ignore[arg-type]
        lock=cast("object", TraceLock(trace)),  # type: ignore[arg-type]
        refs=None,  # type: ignore[arg-type]
    )


def _hooks(trace: Trace) -> tuple[object, ...]:
    async def step() -> None:
        trace.log.append("step")

    async def look_fn() -> Look:
        trace.log.append("look")
        return Look(b"", b"", (), "u")

    async def prepare() -> None:
        trace.log.append("prepare")

    async def settled(before: bytes) -> None:
        trace.log.append(f"settled {before.decode()}")

    return step, look_fn, prepare, settled


@pytest.mark.asyncio
async def test_replay_order_without_hooks_takes_no_before_screenshot() -> None:
    t = Trace()
    step, look_fn, _, _ = _hooks(t)
    await act(_session(t), (step,), send_gate=asyncio.Lock(), look_fn=look_fn)  # type: ignore[arg-type]
    assert t.log == ["unlock", "step", "lock", "wait 7", "look"]


@pytest.mark.asyncio
async def test_discovery_order_with_prepare_and_settled() -> None:
    t = Trace()
    step, look_fn, prepare, settled = _hooks(t)
    await act(
        _session(t),
        (step, step),  # type: ignore[arg-type]
        send_gate=asyncio.Lock(),
        look_fn=look_fn,  # type: ignore[arg-type]
        prepare=prepare,  # type: ignore[arg-type]
        settled=settled,  # type: ignore[arg-type]
    )
    assert t.log == [
        "screenshot",
        "prepare",
        "unlock",
        "step",
        "step",
        "lock",
        "wait 7",
        "settled before",
        "look",
    ]


@pytest.mark.asyncio
async def test_act_waits_for_a_held_send_before_looking() -> None:
    t = Trace()
    step, look_fn, _, _ = _hooks(t)
    gate = asyncio.Lock()
    await gate.acquire()
    task = asyncio.create_task(act(_session(t), (step,), send_gate=gate, look_fn=look_fn))  # type: ignore[arg-type]
    await asyncio.sleep(0.01)
    assert "look" not in t.log
    gate.release()
    await task
    assert t.log[-1] == "look"


def _png(v: int) -> bytes:
    return cv2.imencode(".png", np.full((10, 10, 3), v, np.uint8))[1].tobytes()


class ShotsPage:
    def __init__(self, shots: list[bytes]) -> None:
        self.shots, self.waits = shots, 0

    async def wait_for_timeout(self, ms: int) -> None:
        self.waits += 1

    async def screenshot(self) -> bytes:
        return self.shots.pop(0) if len(self.shots) > 1 else self.shots[0]


@pytest.mark.asyncio
async def test_wait_for_change_returns_once_changed_and_stable() -> None:
    page = ShotsPage([_png(0), _png(200), _png(200), _png(100)])
    await wait_for_change(page, _png(0), 5000, BrowserConfig(settle_ms=0))  # type: ignore[arg-type]
    assert page.waits == len(["changed", "stable", "returned"])


@pytest.mark.asyncio
async def test_wait_for_change_gives_up_after_the_budget() -> None:
    page = ShotsPage([_png(0)])
    await wait_for_change(page, _png(0), 20, BrowserConfig(settle_ms=1))  # type: ignore[arg-type]
    assert page.waits >= 1


class FocusPage:
    """Records the order of calls: keystrokes must come after the site tab is brought to front."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.mouse, self.keyboard = self, self

    async def bring_to_front(self) -> None:
        self.calls.append("front")

    async def click(self, *_: float) -> None:
        self.calls.append("click")

    async def press(self, key: str) -> None:
        self.calls.append(f"press {key}")

    async def type(self, text: str) -> None:
        self.calls.append("type")


@pytest.mark.asyncio
async def test_the_site_tab_is_focused_before_any_keystroke() -> None:
    """Live: login typed into nothing ('please enter a username and password') until a take-over
    had brought the site tab to the front; the control tab held the keyboard."""
    page = FocusPage()
    for step in into_box(page, None, (10, 10), "x"):  # type: ignore[arg-type]
        await step()
    assert page.calls[0] == "front"
    assert page.calls.index("front") < page.calls.index("type")

"""Take-over pieces and their timing (review focus 1): Done in the panel vs the toolbar button
while a send is held at the gates, run against the unified ControlWindow with fakes."""

from __future__ import annotations

import asyncio

import pytest

from cua.config import BrowserConfig
from cua.handoff.control_window import ControlWindow, replay_control
from cua.handoff.extension import handback_button
from cua.handoff.takeover import hand_back, takeover_text, wait_held_send

CFG = BrowserConfig(ext_s=0.05, ext_poll_s=0.01)


class Win:
    def __init__(self) -> None:
        self.html, self.fronted = "", 0

    async def set_content(self, content: str) -> None:
        self.html = content

    def is_closed(self) -> bool:
        return False

    async def bring_to_front(self) -> None:
        self.fronted += 1


class Ext:
    def __init__(self) -> None:
        self.clicks, self.calls = 0, list[str]()

    async def evaluate(self, script: str) -> object:
        self.calls.append(script)
        return self.clicks if "handbackClicked" in script else None


def _modes(cw: ControlWindow) -> list[str]:
    return [q[2] for _, q in cw._stack]


async def _until(cond: object, limit: float = 1.0) -> None:
    loop = asyncio.get_running_loop()
    end = loop.time() + limit
    while not cond():  # type: ignore[operator]
        assert loop.time() < end, "timed out"
        await asyncio.sleep(0.005)


def test_takeover_text_points_at_the_toolbar_button() -> None:
    text = takeover_text()
    assert "click the Agent hand-back icon in the browser toolbar" in text
    assert "puzzle-piece" in text
    assert "Done in the Agent control tab" in text


@pytest.mark.asyncio
async def test_done_in_the_panel_hands_back_and_leaves_no_task() -> None:
    cw = replay_control(Win(), Win())
    button: asyncio.Future[None] = asyncio.get_running_loop().create_future()
    before = asyncio.all_tasks()
    task = asyncio.create_task(hand_back(cw, button, takeover_text()))
    await _until(lambda: _modes(cw) == ["takeover"])
    cw.on_reply("done")
    await asyncio.wait_for(task, 1)
    assert _modes(cw) == []
    assert asyncio.all_tasks() == before


@pytest.mark.asyncio
async def test_the_toolbar_button_hands_back_and_cancels_the_panel() -> None:
    cw, ext = replay_control(Win(), Win()), Ext()
    async with handback_button(ext, CFG) as button:
        task = asyncio.create_task(hand_back(cw, button, takeover_text()))
        await _until(lambda: _modes(cw) == ["takeover"])
        await asyncio.sleep(0.03)
        assert not task.done()  # no click yet: the panel waits, no reminder in between
        ext.clicks += 1
        await asyncio.wait_for(task, 1)
    assert _modes(cw) == []
    assert [c for c in ext.calls if c.startswith("setMode")] == ["setMode('YOU')", "setMode('AI')"]


@pytest.mark.asyncio
async def test_the_panel_is_asked_as_the_human() -> None:
    win = Win()
    cw = replay_control(win, Win())
    button: asyncio.Future[None] = asyncio.get_running_loop().create_future()
    task = asyncio.create_task(hand_back(cw, button, "do it"))
    await _until(lambda: _modes(cw) == ["takeover"])
    assert "In control: human" in win.html
    assert "do it" in win.html
    button.set_result(None)
    await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_wait_held_send_is_true_once_the_gate_is_free() -> None:
    gate = asyncio.Lock()
    assert await wait_held_send(gate, 0.1) is True
    assert not gate.locked()


@pytest.mark.asyncio
async def test_wait_held_send_is_false_when_a_send_stays_held() -> None:
    gate = asyncio.Lock()
    await gate.acquire()  # a guard_send that never finishes
    assert await wait_held_send(gate, 0.05) is False
    assert gate.locked()


@pytest.mark.asyncio
async def test_done_while_a_send_is_held_waits_for_that_gate() -> None:
    """The human pressed Pay (send held, its gate on top of the take-over), then Done on the
    toolbar. Hand-back finishes, then waits for the gate; answering the gate frees both."""
    cw, ext, gate = replay_control(Win(), Win()), Ext(), asyncio.Lock()

    async def held_send() -> str | None:
        async with gate:
            return await cw.ask("Gate 1 of 2", "", "confirm")

    async with handback_button(ext, CFG) as button:
        task = asyncio.create_task(hand_back(cw, button, takeover_text()))
        await _until(lambda: _modes(cw) == ["takeover"])
        send = asyncio.create_task(held_send())
        await _until(lambda: _modes(cw) == ["takeover", "confirm"])
        ext.clicks += 1  # Done on the toolbar while the gate is on screen
        await asyncio.wait_for(task, 1)
    assert _modes(cw) == ["confirm"]  # the gate stays, the take-over panel is gone
    waited = asyncio.create_task(wait_held_send(gate, 1))
    await asyncio.sleep(0.02)
    assert not waited.done()  # held: hand-back waits for it
    cw.on_reply("approve")
    assert await asyncio.wait_for(waited, 1) is True
    assert await send == "approve"


@pytest.mark.asyncio
async def test_panel_done_answers_the_takeover_under_a_gate() -> None:
    """Done in the panel (answer by mode) reaches the take-over even with a gate on top."""
    cw = replay_control(Win(), Win())
    button: asyncio.Future[None] = asyncio.get_running_loop().create_future()
    task = asyncio.create_task(hand_back(cw, button, takeover_text()))
    await _until(lambda: _modes(cw) == ["takeover"])
    gate = asyncio.create_task(cw.ask("Gate 1 of 2", "", "confirm"))
    await _until(lambda: _modes(cw) == ["takeover", "confirm"])
    cw.answer("takeover", "done")
    await asyncio.wait_for(task, 1)
    assert not gate.done()
    cw.on_reply("approve")
    assert await gate == "approve"

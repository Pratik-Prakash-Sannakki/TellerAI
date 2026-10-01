"""ControlWindow: one class, both sides' behaviour.

Ported from tests/discovery/test_control_form.py.

Every old test runs against a discovery-configured and a replay-configured window. The side-only
differences (labels, the form note, replay's closed-window guards, the ``_front`` placement) are
pinned separately below.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

import pytest

from cua.handoff.control_window import ControlWindow, discovery_control, replay_control


class FakeWin:
    def __init__(self) -> None:
        self.html, self.fronted, self.closed = "", 0, False
        self.fail_content = self.fail_front = False

    async def set_content(self, content: str) -> None:
        if self.fail_content:
            raise RuntimeError("Target closed")
        self.html = content

    def is_closed(self) -> bool:
        return self.closed

    async def bring_to_front(self) -> None:
        if self.fail_front:
            raise RuntimeError("Target closed")
        self.fronted += 1


Factory = Callable[[FakeWin, FakeWin], ControlWindow]
SIDES = pytest.mark.parametrize(
    "make", [discovery_control, replay_control], ids=["agent", "replay"]
)


def _window(make: Factory) -> tuple[ControlWindow, FakeWin, FakeWin]:
    win, site = FakeWin(), FakeWin()
    return make(win, site), win, site


async def _settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


@SIDES
@pytest.mark.asyncio
async def test_form_returns_answers_and_masks_sensitive(make: Factory) -> None:
    cw, win, site = _window(make)
    task = asyncio.create_task(cw.form("Fill", [("Address", False), ("Password", True)]))
    await _settle()
    assert "type=text" in win.html
    assert "type=password" in win.html
    cw.on_reply(json.dumps(["12 Main St", "x"]))
    assert await task == ["12 Main St", "x"]
    assert win.fronted == 1
    assert site.fronted == 1


@SIDES
@pytest.mark.asyncio
async def test_gate_supersedes_takeover_then_restores_it(make: Factory) -> None:
    """Regression: a gate during a take-over must win, then hand the take-over back intact."""
    cw, win, _ = _window(make)
    takeover = asyncio.create_task(cw.ask("You are in control", "", "takeover"))
    await _settle()
    gate = asyncio.create_task(cw.ask("Gate 1 of 2", "", "approve"))
    await _settle()
    assert "Gate 1 of 2" in win.html  # the gate is on screen now
    cw.on_reply("approve")  # answers the gate, not the take-over
    assert await gate == "approve"
    assert not takeover.done()
    await _settle()
    assert "You are in control" in win.html  # take-over is back
    cw.on_reply("done")
    assert await takeover == "done"


@SIDES
@pytest.mark.asyncio
async def test_closing_the_window_fails_every_question_closed(make: Factory) -> None:
    cw, _, _ = _window(make)
    a = asyncio.create_task(cw.ask("a", "", "takeover"))
    b = asyncio.create_task(cw.ask("b", "", "approve"))
    await _settle()
    cw.on_reply(None)
    assert await a is None
    assert await b is None


@SIDES
@pytest.mark.asyncio
async def test_dropdown_row_lists_every_option(make: Factory) -> None:
    cw, win, _ = _window(make)
    task = asyncio.create_task(
        cw.form("Fill", [("From account", False)], options=[["13344", "14898", "15009"]])
    )
    await _settle()
    assert (
        "<select class=f><option>13344</option><option>14898</option><option>15009</option>"
        in win.html
    )
    assert "Options:" not in win.html
    cw.on_reply(json.dumps(["14898"]))
    assert await task == ["14898"]


@SIDES
@pytest.mark.asyncio
async def test_answer_finds_the_takeover_under_a_gate(make: Factory) -> None:
    cw, _, _ = _window(make)
    takeover = asyncio.create_task(cw.ask("You are in control", "", "takeover"))
    await _settle()
    gate = asyncio.create_task(cw.ask("Gate 1 of 2", "", "confirm"))
    await _settle()
    cw.answer("takeover", "done")
    assert await takeover == "done"
    assert not gate.done()
    cw.on_reply("approve")
    assert await gate == "approve"


# --- side-specific text -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("make", "label", "who", "working"),
    [
        (discovery_control, "Done, hand back to agent", "agent", "Agent is working"),
        (replay_control, "Done, hand back to replay", "replay", "Replay is working"),
    ],
)
@pytest.mark.asyncio
async def test_each_side_keeps_its_own_labels(
    make: Factory, label: str, who: str, working: str
) -> None:
    cw, win, _ = _window(make)
    task = asyncio.create_task(cw.ask("You are in control", "", "takeover"))
    await _settle()
    assert label in win.html
    assert f"In control: {who}" in win.html
    cw.on_reply("done")
    await task
    assert f"<h3>{working}</h3>" in win.html


@pytest.mark.parametrize(
    ("make", "note"),
    [
        (discovery_control, "Our code enters these into the site. The agent never sees them."),
        (replay_control, "Our code enters these into the site.</div>"),
    ],
)
@pytest.mark.asyncio
async def test_each_side_keeps_its_own_form_note(make: Factory, note: str) -> None:
    cw, win, _ = _window(make)
    task = asyncio.create_task(cw.form("Fill", [("Address", False)]))
    await _settle()
    assert note in win.html
    cw.on_reply("")
    assert await task is None


@pytest.mark.parametrize(
    ("make", "mode"),
    [(discovery_control, "help"), (discovery_control, "text"), (replay_control, "rescue")],
)
@pytest.mark.asyncio
async def test_every_mode_of_both_sides_renders(make: Factory, mode: str) -> None:
    cw, win, _ = _window(make)
    await cw.show("t", mode=mode)
    assert "cuaReply" in win.html


# --- replay's closed-window guards (discovery has none) -----------------------------------------


@pytest.mark.asyncio
async def test_replay_ask_on_a_closed_window_returns_none_at_once() -> None:
    cw, win, _ = _window(replay_control)
    win.closed = True
    assert await cw.ask("t", "", "approve") is None
    assert win.html == ""


@pytest.mark.asyncio
async def test_replay_set_content_failure_fails_the_question_closed() -> None:
    cw, win, _ = _window(replay_control)
    win.fail_content = True
    assert await asyncio.wait_for(cw.ask("t", "", "approve"), 1) is None


@pytest.mark.asyncio
async def test_discovery_has_no_closed_window_guard() -> None:
    cw, win, _ = _window(discovery_control)
    win.closed = True
    await cw.show("still drawn")
    assert "still drawn" in win.html


@pytest.mark.asyncio
async def test_replay_skips_bringing_a_closed_site_tab_to_front() -> None:
    cw, win, site = _window(replay_control)
    site.closed = True
    task = asyncio.create_task(cw.ask("t", "", "approve"))
    await _settle()
    cw.on_reply("approve")
    assert await task == "approve"
    assert site.fronted == 0


@pytest.mark.parametrize(("make", "kept"), [(discovery_control, 0), (replay_control, 1)])
@pytest.mark.asyncio
async def test_front_placement_differs_per_side(make: Factory, kept: int) -> None:
    """Discovery calls _front inside try (the question is removed on failure); replay before it."""
    cw, win, _ = _window(make)
    win.fail_front = True
    with pytest.raises(RuntimeError):
        await cw.ask("t", "", "approve")
    assert len(cw._stack) == kept

"""human_help / take_over / offer_control / human_fills, against the unified ControlWindow.

Ported from tests/discovery/test_human_help.py, test_handback.py and test_choose_option.py.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable

import pytest

from cua.config import DiscoveryConfig
from cua.discovery.context import Ctx
from cua.discovery.tools import human
from cua.discovery.tools.human import human_fills, human_help, offer_control, take_over
from cua.vision.look import Look
from tests.fakes import FakeTab, make_ctx, make_session

SITE_URL = "https://example.test/app/x"


class Ext:
    """The hand-back extension's service worker: a click counter and a badge. Never the site."""

    def __init__(self, hang: bool = False, fail: bool = False) -> None:
        self.clicks, self.calls, self.hang, self.fail = 0, list[str](), hang, fail

    async def evaluate(self, script: str) -> object:
        self.calls.append(script)
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise TimeoutError("Target closed")
        return self.clicks if "handbackClicked" in script else None


def _ctx(ext: object | None = None, handback_s: float = 2) -> tuple[Ctx, FakeTab]:
    page = FakeTab(SITE_URL)
    ctx = make_ctx(make_session(page, ext=ext), DiscoveryConfig(handback_s=handback_s))  # type: ignore[arg-type]
    return ctx, page


def _modes(ctx: Ctx) -> list[str]:
    return [q[2] for _, q in ctx.control._stack]


async def _until(cond: Callable[[], bool], limit: float = 1.0) -> None:
    end = time.monotonic() + limit
    while not cond():
        assert time.monotonic() < end, "timed out"
        await asyncio.sleep(0.005)


async def _answer(ctx: Ctx, mode: str, value: str) -> None:
    await _until(lambda: mode in _modes(ctx))
    ctx.control.answer(mode, value)


async def _help_then(
    ctx: Ctx, choice: str, after: Callable[[], Awaitable[None]] | None = None
) -> str:
    task = asyncio.create_task(human_help(ctx, "t", "why"))
    await _answer(ctx, "help", choice)
    if after:
        await after()
    return await asyncio.wait_for(task, 2)


def _dirty(ctx: Ctx) -> None:
    r = ctx.run
    r.stuck, r.recent, r.fails, r.steps, r.login_blocked, r.login_tries = "x", ["a"], 3, 9, True, 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("answer", "start", "reset"),
    [
        ("say:use the checking account", "The human says: use the checking account", True),
        ("takeover", "A human took over", True),
        ("stop", "STOPPED", False),
    ],
)
async def test_outcomes(answer: str, start: str, reset: bool) -> None:
    ctx, _ = _ctx()
    _dirty(ctx)

    async def done() -> None:
        await _answer(ctx, "takeover", "done")

    out = await _help_then(ctx, answer, done if answer == "takeover" else None)
    assert out.startswith(start)
    assert (ctx.run.fails == 0 and ctx.run.steps == 0 and ctx.run.stuck == "") is reset
    assert ctx.run.given == (["use the checking account"] if answer.startswith("say:") else [])


@pytest.mark.asyncio
async def test_a_closed_window_stops_the_run() -> None:
    ctx, _ = _ctx()
    task = asyncio.create_task(human_help(ctx, "t", "why"))
    await _until(lambda: _modes(ctx) == ["help"])
    ctx.control.on_reply(None)
    assert (await task).startswith("STOPPED")
    assert ctx.run.log[-1]["tool"] == "stuck"


async def _take_over(ctx: Ctx, during: Callable[[], None]) -> str | None:
    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    during()
    ctx.control.on_reply("done")
    return await asyncio.wait_for(task, 2)


@pytest.mark.asyncio
async def test_take_over_records_page_paths_and_sends_as_evidence() -> None:
    ctx, page = _ctx()

    def human_acts() -> None:
        page.navigate("https://example.test/app/billpay.htm?payee=Sean&amount=10")
        page.navigate("https://ads.example/frame?x=1", iframe=True)  # not the main frame
        assert ctx.run.takeover is not None
        ctx.run.takeover.append({"kind": "send", "path": "/app/services/bank/billpay"})
        page.navigate("https://example.test/app/overview.htm")

    assert await _take_over(ctx, human_acts) is None
    ev = ctx.run.log[-1]
    assert ev["tool"] == "take_over"
    assert ev["recordable"] is False
    assert ev["human_entry"] is True
    assert ev["actions"] == [
        {"kind": "page", "path": "/app/billpay.htm"},
        {"kind": "send", "path": "/app/services/bank/billpay"},
        {"kind": "page", "path": "/app/overview.htm"},
    ]
    assert "Sean" not in str(ev["actions"])
    assert "amount" not in str(ev["actions"])
    assert ev["shot_before"] == b"shot1"
    assert ev["shot_after"] == b"shot2"
    assert ev["url_before"] == "/app/x"


@pytest.mark.asyncio
async def test_listener_is_removed_and_secrets_reset_after_hand_back() -> None:
    ctx, page = _ctx()
    ctx.run.typed_secrets = {"username"}
    await _take_over(ctx, lambda: None)
    assert page.handlers["framenavigated"] == []
    assert ctx.run.takeover is None
    assert ctx.run.typed_secrets == set()
    assert ctx.run.dropdowns == []


@pytest.mark.asyncio
async def test_a_page_off_the_site_goes_back_to_the_start() -> None:
    ctx, page = _ctx()
    await _take_over(ctx, lambda: page.navigate("https://elsewhere.example/"))
    assert page.url == "https://example.test/app"


@pytest.mark.asyncio
async def test_a_screenshot_that_times_out_still_hands_back_cleanly() -> None:
    ctx, page = _ctx()
    page.hangs = True
    await _take_over(ctx, lambda: None)
    ev = ctx.run.log[-1]
    assert ev["shot_before"] is None
    assert ev["shot_after"] is None
    assert page.handlers["framenavigated"] == []
    assert ctx.run.takeover is None


@pytest.mark.asyncio
async def test_no_deadlock_when_a_gate_is_pending_at_done() -> None:
    """Review focus 1: Done while a send is held at the gates waits for that gate."""
    ctx, _ = _ctx()
    helped = asyncio.create_task(human_help(ctx, "t", "why"))
    await _answer(ctx, "help", "takeover")
    await _until(lambda: _modes(ctx) == ["takeover"])

    async def gate_held() -> None:
        async with ctx.guard.lock:
            await ctx.control.ask("Gate 1 of 2", "", "confirm")

    held = asyncio.create_task(gate_held())
    await _until(lambda: "confirm" in _modes(ctx))
    ctx.control.answer("takeover", "done")  # Done while the gate is pending
    await asyncio.sleep(0.01)
    assert not helped.done()
    ctx.control.answer("confirm", "approve")
    out, _ = await asyncio.wait_for(asyncio.gather(helped, held), 2)
    assert out.startswith("A human took over")
    assert ctx.run.log[-1]["tool"] == "take_over"


@pytest.mark.asyncio
async def test_done_with_a_send_held_forever_ends_the_take_over_as_stuck() -> None:
    ctx, page = _ctx(handback_s=0.05)
    await ctx.guard.lock.acquire()  # a guard that never finishes
    out = await _help_then(ctx, "takeover", lambda: _answer(ctx, "takeover", "done"))
    assert out.startswith("STUCK: a send the human started was still held")
    assert page.handlers["framenavigated"] == []
    assert ctx.run.takeover is None
    assert [e["tool"] for e in ctx.run.log] == ["take_over"]


# --- the toolbar hand-back button (was test_handback.py) ---


def _badge(ext: Ext) -> list[str]:
    return [c for c in ext.calls if c.startswith("setMode")]


@pytest.mark.asyncio
async def test_done_in_the_takeover_itself_cancels_the_watcher() -> None:
    ctx, _ = _ctx(Ext())
    before = asyncio.all_tasks()
    await _take_over(ctx, lambda: None)
    await asyncio.sleep(0.15)
    assert asyncio.all_tasks() == before
    assert _modes(ctx) == []


@pytest.mark.asyncio
async def test_the_badge_reads_you_during_the_take_over_then_ai() -> None:
    ext = Ext()
    ctx, _ = _ctx(ext)
    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    assert _badge(ext) == ["setMode('YOU')"]
    ctx.control.on_reply("done")
    await asyncio.wait_for(task, 1)
    assert _badge(ext) == ["setMode('YOU')", "setMode('AI')"]


@pytest.mark.asyncio
async def test_a_click_on_the_toolbar_button_hands_back() -> None:
    ext = Ext()
    ext.clicks = 4  # clicks from an earlier take-over
    ctx, page = _ctx(ext)
    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    await asyncio.sleep(0.05)
    assert not task.done()  # the old count is the baseline
    ext.clicks += 1
    assert await asyncio.wait_for(task, 1) is None
    # only what take_over did before the button existed: listen, screenshot, front
    assert set(page.calls) <= {"on", "remove_listener", "screenshot", "bring_to_front"}


@pytest.mark.asyncio
async def test_the_button_poll_is_cancelled_even_when_the_take_over_fails() -> None:
    ext = Ext()
    ctx, _ = _ctx(ext)
    before = asyncio.all_tasks()

    class Boom(Exception):
        pass

    async def broken() -> bool:
        raise Boom

    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    ctx.guard.lock.acquire = broken  # type: ignore[method-assign]
    ctx.control.on_reply("done")
    with contextlib.suppress(Boom):
        await asyncio.wait_for(task, 1)
    await asyncio.sleep(0.05)
    assert asyncio.all_tasks() == before
    assert _badge(ext)[-1] == "setMode('AI')"
    assert ctx.run.takeover is None


@pytest.mark.asyncio
@pytest.mark.parametrize("ext", [None, Ext(fail=True), Ext(hang=True)])
async def test_no_extension_still_hands_back_from_the_control_tab(ext: Ext | None) -> None:
    ctx, _ = _ctx(ext)
    assert await _take_over(ctx, lambda: None) is None


@pytest.mark.asyncio
async def test_no_idle_reminder_ever_interrupts_the_take_over() -> None:
    ctx, _ = _ctx()
    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    await asyncio.sleep(0.3)
    assert _modes(ctx) == ["takeover"]
    ctx.control.on_reply("done")
    await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_take_over_message_points_at_the_toolbar_button() -> None:
    ctx, _ = _ctx()
    task = asyncio.create_task(take_over(ctx, "why"))
    await _until(lambda: _modes(ctx) == ["takeover"])
    assert "click the Agent hand-back icon in the browser toolbar" in ctx.control._stack[0][1][1]
    ctx.control.on_reply("done")
    await task


# --- offer_control (was test_choose_option.py) ---


@pytest.mark.asyncio
async def test_offer_control_shows_only_the_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    got: list[tuple[str, str]] = []

    async def fake(ctx: object, title: str, reason: str) -> str:
        got.append((title, reason))
        return "ok"

    monkeypatch.setattr(human, "human_help", fake)
    msg = "STUCK: not in the list: From account #\nURL: x\nText on screen:\n[1] 'a'"
    await offer_control(make_ctx(), msg)
    assert got == [("The agent is stuck", "not in the list: From account #")]


# --- human_fills ---


@pytest.fixture
def entry(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """No page: options come from a stub, entry is recorded, the look is a blank one."""
    did: list[str] = []

    async def no_options(ctx: object, point: tuple[int, int]) -> list[str]:
        return []

    async def typed(ctx: object, *steps: object) -> Look:
        did.append("act")
        return Look(b"", b"", (), "u")

    monkeypatch.setattr(human, "list_options", no_options)
    monkeypatch.setattr(human, "act", typed)
    monkeypatch.setattr(human, "crop", lambda *a: b"crop")
    return did


async def _fill(ctx: Ctx, answer: str | None, fields: list[tuple[tuple[int, int], str]]) -> str:
    task = asyncio.create_task(human_fills(ctx, fields))
    await _until(lambda: _modes(ctx) == ["form"])
    ctx.control.on_reply(answer)
    return await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_human_fills_enters_values_and_never_logs_them(entry: list[str]) -> None:
    ctx = make_ctx()
    ctx.run.look = Look(b"", b"", (), "u")
    out = await _fill(ctx, '["90210", "123-45"]', [((5, 5), "Zip"), ((5, 9), "SSN")])
    assert out.startswith("A human gave: Zip, SSN")
    assert entry == ["act", "act"]
    assert ctx.run.entered == {"Zip": "90210", "SSN": "******"}
    assert ctx.run.given == ["90210"]
    assert [e["tool"] for e in ctx.run.log] == ["request_value", "request_value"]
    assert "90210" not in str(ctx.run.log)
    assert "123-45" not in str(ctx.run.log)
    assert [e.get("shapes") for e in ctx.run.log] == [["number", "integer", "id"], None]


@pytest.mark.asyncio
async def test_human_fills_with_no_values_skips(entry: list[str]) -> None:
    ctx = make_ctx()
    ctx.run.look = Look(b"", b"", (), "u")
    assert (await _fill(ctx, None, [((5, 5), "Zip")])).startswith("SKIPPED")
    assert entry == []

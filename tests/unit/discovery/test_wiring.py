"""attach / new_run and the page wrappers (look, act, snap) over fakes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest

from cua.config import DiscoveryConfig
from cua.discovery import context, wiring
from cua.discovery.context import act, canvas, look, snap, to_page
from cua.discovery.run import DiscoveryRun
from cua.discovery.wiring import attach, new_run
from cua.safety import SendGuard
from cua.vision.look import Box, Element, Look
from tests.fakes import FakeRoute, FakeTab, make_ctx, make_session

SECRETS = {"username": "u-val", "password": "p-val"}


@pytest.mark.asyncio
async def test_attach_routes_the_guard_and_opens_the_control_window() -> None:
    page, ctl = FakeTab(), FakeTab("about:blank")
    ctx = await attach(make_session(page, ctl), DiscoveryConfig(), SECRETS)
    assert page.calls[:2] == ["unroute", "route"]
    assert page.routes == [ctx.guard]
    assert isinstance(ctx.guard, SendGuard)
    assert ctx.guard.state is ctx.run
    assert "Agent is working" in ctl.html
    assert page.calls[-1] == "bring_to_front"
    task = asyncio.create_task(ctx.control.ask("q", "", "approve"))  # cuaReply answers ctx.control
    await asyncio.sleep(0)
    ctl.exposed["cuaReply"]("reject")
    assert await asyncio.wait_for(task, 1) == "reject"


@pytest.mark.asyncio
async def test_attach_twice_on_the_same_page_is_re_run_safe() -> None:
    """Review focus 3: a notebook re-run unroutes, routes again, tolerates 'already registered'."""
    page, ctl = FakeTab(), FakeTab("about:blank")
    session = make_session(page, ctl)
    first = await attach(session, DiscoveryConfig(), SECRETS)
    second = await attach(session, DiscoveryConfig(), SECRETS)
    assert page.calls.count("unroute") == 2  # noqa: PLR2004
    assert page.routes == [second.guard]
    assert second.guard is not first.guard


@pytest.mark.asyncio
async def test_attach_raises_any_other_expose_error() -> None:
    ctl = FakeTab("about:blank")

    async def broken(name: str, fn: Callable[..., object]) -> None:
        raise RuntimeError("Target closed")

    ctl.expose_function = broken  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="Target closed"):
        await attach(make_session(control_page=ctl), DiscoveryConfig(), SECRETS)


@pytest.mark.asyncio
async def test_main_frame_navigations_are_counted_on_the_current_run() -> None:
    page = FakeTab()
    ctx = await attach(make_session(page), DiscoveryConfig(), SECRETS)
    page.navigate("https://example.test/a")
    page.navigate("https://ads.example/f", iframe=True)
    assert ctx.run.navs == 1
    ctx = new_run(ctx, "next goal")
    page.navigate("https://example.test/b")
    assert ctx.run.navs == 1


@pytest.mark.asyncio
async def test_closing_the_control_tab_answers_every_question_none() -> None:
    ctl = FakeTab("about:blank")
    ctx = await attach(make_session(control_page=ctl), DiscoveryConfig(), SECRETS)
    task = asyncio.create_task(ctx.control.ask("q", "", "approve"))
    await asyncio.sleep(0)
    ctl.emit("close", None)
    assert await task is None


@pytest.mark.asyncio
async def test_new_run_swaps_the_run_the_guard_reads() -> None:
    ctx = await attach(make_session(), DiscoveryConfig(), SECRETS)
    old = ctx.run
    old.given.append("x")
    ctx2 = new_run(ctx, "pay 10")
    assert ctx2.run is not old
    assert ctx2.run.goal == "pay 10"
    assert ctx2.run.given == []
    assert ctx2.guard is ctx.guard
    assert ctx.guard.state is ctx2.run
    assert ctx.run is ctx2.run


@pytest.mark.asyncio
async def test_the_guard_writes_its_verdict_on_the_current_run() -> None:
    ctx = new_run(await attach(make_session(), DiscoveryConfig(), SECRETS), "g")
    ctx.run.allow_send = True
    route = FakeRoute("POST", "https://example.test/login", "a=1")
    await ctx.guard(route)
    assert route.calls == [("continue_", {})]


@pytest.mark.asyncio
async def test_on_sent_hooks_redact_log_dropdowns_and_clear_entered() -> None:
    ctx = new_run(await attach(make_session(), DiscoveryConfig(), SECRETS), "send 10 to 14898")
    ctx.run.entered = {"Amount": "10"}
    ctx.run.takeover = []
    task = asyncio.create_task(
        ctx.guard(FakeRoute("POST", "https://example.test/app/transfer", "amount=10&to=14898"))
    )
    for mode in ("confirm", "approve"):
        while not any(q[2] == mode for _, q in ctx.control._stack):
            await asyncio.sleep(0.001)
        ctx.control.answer(mode, "approve")
    await asyncio.wait_for(task, 1)
    assert {"10", "14898"} <= ctx.run.redact
    assert ctx.run.entered == {}
    assert ctx.run.verdict.startswith("SENT")
    assert ctx.run.log[-1]["tool"] == "send"
    assert ctx.run.log[-1]["args"] == {"path": "/app/transfer"}
    assert ctx.run.log[-1]["corrected"] == []
    assert ctx.run.takeover == [{"kind": "send", "path": "/app/transfer"}]


def _look() -> Look:
    return Look(b"png", b"drawn", (Element(1, "Accounts Overview", Box(0, 0, 9, 9)),), "u", 2.0)


@pytest.mark.asyncio
async def test_look_stores_it_on_the_run_and_counts_start_page_texts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_take_look(
        page: object, cfg: object, refs: object, on_look: Callable[[Look], None]
    ) -> Look:
        lk = _look()
        on_look(lk)
        return lk

    monkeypatch.setattr(context, "take_look", fake_take_look)
    ctx = make_ctx()
    ctx.run.log.append(
        {"tool": "start", "args": {}, "result": "", "point": None, "url": "u", "crop": None}
    )
    await look(ctx)
    got = await look(ctx)
    start = ctx.run.log[0]
    assert ctx.run.look is got
    assert start["looks"] == 2  # noqa: PLR2004
    assert start["start_texts"] == ["Accounts Overview"]
    assert start["text_counts"] == {"accounts overview": 2}


@pytest.mark.asyncio
async def test_look_without_a_start_event_only_stores_the_look(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_take_look(
        page: object, cfg: object, refs: object, on_look: Callable[[Look], None]
    ) -> Look:
        lk = _look()
        on_look(lk)
        return lk

    monkeypatch.setattr(context, "take_look", fake_take_look)
    ctx = make_ctx()
    assert await look(ctx) is ctx.run.look
    assert ctx.run.log == []


def test_canvas_and_to_page_follow_the_current_look() -> None:
    ctx = make_ctx()
    assert canvas(ctx) == (1280, 800)
    assert to_page(ctx, (3, 4)) == (3, 4)
    ctx.run.look = _look()
    assert to_page(ctx, (3, 4)) == (6.0, 8.0)


@pytest.mark.asyncio
async def test_snap_never_raises_on_a_held_page() -> None:
    page = FakeTab()
    page.hangs = True
    assert await snap(make_ctx(make_session(page))) is None


@pytest.mark.asyncio
async def test_act_reads_dropdowns_first_and_waits_for_a_response_after_a_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace: list[str] = []
    ctx = make_ctx()

    async def dropdowns(page: object, script: str, timeout_s: float) -> list[dict[str, object]]:
        trace.append(f"dropdowns {timeout_s}")
        return [{"value": "1"}]

    async def changed(page: object, before: bytes, wait_ms: int, cfg: object) -> None:
        trace.append(f"changed {before.decode()} {wait_ms}")

    async def fake_look(c: object) -> Look:
        trace.append("look")
        return _look()

    async def step() -> None:
        trace.append("step")
        ctx.run.verdict = "SENT: a human approved both gates."

    monkeypatch.setattr(context, "read_dropdowns", dropdowns)
    monkeypatch.setattr(context, "wait_for_change", changed)
    monkeypatch.setattr(context, "look", fake_look)
    await act(ctx, step)
    assert trace == ["dropdowns 3.0", "step", "changed shot1 8000", "look"]
    assert ctx.run.dropdowns == [{"value": "1"}]


@pytest.mark.asyncio
async def test_act_without_a_send_does_not_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = make_ctx()
    waited: list[bytes] = []

    async def none(*a: object) -> list[object]:
        return []

    async def changed(page: object, before: bytes, *a: object) -> None:
        waited.append(before)

    async def fake_look(c: object) -> Look:
        return _look()

    monkeypatch.setattr(context, "read_dropdowns", none)
    monkeypatch.setattr(context, "wait_for_change", changed)
    monkeypatch.setattr(context, "look", fake_look)
    await act(ctx)
    assert waited == []


def test_wiring_module_exposes_build_ctx() -> None:
    assert callable(wiring.build_ctx)
    assert isinstance(make_ctx().run, DiscoveryRun)


@pytest.mark.asyncio
async def test_after_a_re_run_the_exposed_reply_answers_the_second_window() -> None:
    """C1: one cuaReply forwarder per control page, dispatching to the current window."""
    ctl = FakeTab("about:blank")
    session = make_session(control_page=ctl)
    await attach(session, DiscoveryConfig(), SECRETS)
    second = await attach(session, DiscoveryConfig(), SECRETS)
    task = asyncio.create_task(second.control.ask("q", "", "approve"))
    await asyncio.sleep(0)
    ctl.exposed["cuaReply"]("approve")
    assert await asyncio.wait_for(task, 1) == "approve"


@pytest.mark.asyncio
async def test_after_a_re_run_one_close_listener_closes_the_second_window() -> None:
    ctl = FakeTab("about:blank")
    session = make_session(control_page=ctl)
    await attach(session, DiscoveryConfig(), SECRETS)
    second = await attach(session, DiscoveryConfig(), SECRETS)
    assert len(ctl.handlers["close"]) == 1
    task = asyncio.create_task(second.control.ask("q", "", "approve"))
    await asyncio.sleep(0)
    ctl.emit("close", None)
    assert await asyncio.wait_for(task, 1) is None


@pytest.mark.asyncio
async def test_after_a_re_run_one_nav_listener_counts_on_the_second_ctx() -> None:
    """I1: framenavigated is wired once per page and forwards to the current ctx."""
    page = FakeTab()
    session = make_session(page)
    first = await attach(session, DiscoveryConfig(), SECRETS)
    second = await attach(session, DiscoveryConfig(), SECRETS)
    assert len(page.handlers["framenavigated"]) == 1
    page.navigate("https://example.test/a")
    assert second.run.navs == 1
    assert first.run.navs == 0

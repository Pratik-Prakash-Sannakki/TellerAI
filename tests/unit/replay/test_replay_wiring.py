"""attach (the replay setup cell), the guard's replay hooks, and R7: after replay() returns, the
run holds no input values, given text or look (review focus 5)."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from types import SimpleNamespace

import pytest

from cua.config import ReplayConfig, load_site
from cua.handoff.control_window import REPLAY
from cua.replay import engine, loader
from cua.replay.context import Ctx
from cua.replay.run import ReplayRun
from cua.replay.wiring import attach
from cua.safety.send_guard import REPLAY_OPTIONS
from cua.schema import Capability
from tests.fakes import FakeTab
from tests.unit.replay.helpers import make_replay_ctx, mk_look, write_cap

SITE = load_site("parabank")


class Tab:
    def __init__(self, registered: bool = False) -> None:
        self.calls: list[tuple[str, object]] = []
        self.registered = registered
        self.main_frame = object()

    async def unroute(self, pattern: str) -> None:
        self.calls.append(("unroute", pattern))

    async def route(self, pattern: str, handler: object) -> None:
        self.calls.append(("route", handler))

    def on(self, event: str, fn: object) -> None:
        self.calls.append(("on", event))

    async def expose_function(self, name: str, fn: object) -> None:
        if self.registered:
            raise RuntimeError(f'Function "{name}" has been already registered')
        self.calls.append(("expose", name))

    async def set_content(self, html: str) -> None:
        self.calls.append(("set_content", "Replay is working" in html))

    def is_closed(self) -> bool:
        return False

    async def bring_to_front(self) -> None:
        self.calls.append(("front", None))


def _session(page: Tab, control: Tab) -> object:
    ctx = make_replay_ctx(page)
    return dataclasses.replace(ctx.session, control_page=control)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_attach_routes_through_the_guard_and_opens_the_control_window() -> None:
    page, control = Tab(), Tab()
    ctx = await attach(_session(page, control), SITE, ReplayConfig())  # type: ignore[arg-type]
    assert page.calls[:2] == [("unroute", "**/*"), ("route", ctx.guard)]
    assert ("on", "response") in page.calls and page.calls[-1] == ("front", None)
    assert ("expose", "cuaReply") in control.calls and ("on", "close") in control.calls
    assert ("set_content", True) in control.calls
    assert ctx.control.side is REPLAY and ctx.guard.options is REPLAY_OPTIONS
    assert ctx.guard.state is ctx.run


@pytest.mark.asyncio
async def test_attach_rerun_tolerates_an_already_registered_reply_and_one_listener() -> None:
    page, control = Tab(), Tab(registered=True)
    session = _session(page, control)
    await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    assert page.calls.count(("on", "response")) == 1  # once per page, even on a re-run


class Route:
    def __init__(self, method: str = "POST") -> None:
        self.request = type("R", (), {"method": method, "url": "https://x/a", "post_data": ""})()
        self.calls: list[str] = []

    async def continue_(self, **_: object) -> None:
        self.calls.append("continue")

    async def abort(self) -> None:
        self.calls.append("abort")


@pytest.mark.asyncio
async def test_the_guard_hooks_mark_sent_then_gated() -> None:
    ctx = make_replay_ctx(control=None)
    ctx.run.takeover = {"pages": [], "sends": []}

    class No:
        async def ask(self, *a: object, **k: object) -> str:
            return "reject"

    ctx.control = ctx.guard.control = No()  # type: ignore[assignment]
    route = Route()
    await ctx.guard(route)  # type: ignore[arg-type]
    assert ctx.run.sent and ctx.run.gated and ctx.run.takeover["sends"] == ["/a"]
    assert route.calls == ["abort"]


@pytest.mark.asyncio
async def test_after_replay_the_run_holds_no_values_given_text_or_look(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-secret")
    ctx = make_replay_ctx()
    first_run = ctx.run

    async def open_start(c: Ctx, cp: Capability) -> None:
        c.run.look = mk_look([("Sean Park 74838", (0, 0, 9, 9))])

    async def ask_inputs(c: Ctx, cp: Capability, given: dict[str, str]) -> dict[str, str]:
        return {"account_id": "74838"}

    async def finish(c: Ctx, cp: Capability, crops: Path | None, drift: list[object]) -> object:
        c.run.given.append("Sean Park")
        c.run.outputs["balance"] = "$5.00"
        return await engine.stopped(c, engine.Stop("STUCK", "x"), [])  # type: ignore[arg-type]

    async def no_snap(c: Ctx) -> None:
        return None

    monkeypatch.setattr(engine, "open_start", open_start)
    monkeypatch.setattr(loader, "ask_inputs", ask_inputs)
    monkeypatch.setattr(engine, "finish", finish)
    monkeypatch.setattr(engine, "snap", no_snap)
    res = await engine.replay(ctx, write_cap(tmp_path))
    assert res.status == "STUCK" and res.outputs == {"balance": "$5.00"}
    assert ctx.run is not first_run and ctx.run == ReplayRun()
    assert ctx.run.values == {} and ctx.run.given == [] and ctx.run.given_text() == ""
    assert ctx.run.look is None and ctx.run.outputs == {}
    assert ctx.guard.state is ctx.run  # the guard reads the fresh run from now on
    assert ctx.last.values == {"74838", "Sean Park"}  # masking only, memory only


@pytest.mark.asyncio
async def test_the_run_is_wiped_even_when_the_capability_is_invalid(tmp_path: Path) -> None:
    ctx = make_replay_ctx()
    ctx.run.values = {"x": "1"}
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: t\n")
    res = await engine.replay(ctx, bad)
    assert res.status == "FAILED" and res.reason.startswith("invalid capability")
    assert ctx.run == ReplayRun() and ctx.last.values == {"1"}


def _fake_session() -> tuple[FakeTab, FakeTab, object]:
    page, control = FakeTab(), FakeTab("about:blank")
    return page, control, _session(page, control)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_after_a_re_run_the_exposed_reply_and_close_reach_the_second_window() -> None:
    """C1: one cuaReply forwarder and one close listener per control page, both forwarding to the
    window of the latest attach."""
    _, control, session = _fake_session()
    await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    second = await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    assert len(control.handlers["close"]) == 1
    task = asyncio.create_task(second.control.ask("q", "", "approve"))
    await asyncio.sleep(0)
    control.exposed["cuaReply"]("approve")
    assert await asyncio.wait_for(task, 1) == "approve"
    task = asyncio.create_task(second.control.ask("q", "", "approve"))
    await asyncio.sleep(0)
    control.emit("close", None)
    assert await asyncio.wait_for(task, 1) is None


class _Resp:
    def __init__(self, frame: object) -> None:
        self.request = SimpleNamespace(is_navigation_request=lambda: True)
        self.frame, self.status, self.url = frame, 200, "https://example.test/app/b.htm"


@pytest.mark.asyncio
async def test_after_a_re_run_a_navigation_response_updates_the_second_run() -> None:
    """I1: the once-per-page response listener reads the current ctx."""
    page, _, session = _fake_session()
    first = await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    second = await attach(session, SITE, ReplayConfig())  # type: ignore[arg-type]
    assert len(page.handlers["response"]) == 1
    page.emit("response", _Resp(page.main_frame))
    assert second.run.http == (200, "/app/b.htm") and second.run.navs == 1
    assert first.run.navs == 0

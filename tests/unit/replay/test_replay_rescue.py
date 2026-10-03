"""A take-over is recorded as evidence (shots, page paths, send paths, no values) and marks the
result; the toolbar hand-back button; a held send never blocks the gates. Ported from
tests/replay/test_takeover.py and the gate test of test_partial_outputs.py.
"""

from __future__ import annotations

import asyncio

import pytest

from cua.browser.dropdown import DROPDOWNS_JS
from cua.config import ReplayConfig
from cua.replay import engine, rescue, steps
from cua.replay.context import Ctx
from cua.replay.wiring import stash_dropdowns
from cua.schema import Capability, Step, Stop
from cua.vision import Box, Element, Look
from tests.unit.replay.helpers import (
    cap,
    click,
    extract,
    make_replay_ctx,
    mk_look,
    screen,
    set_control,
    type_,
)

LOOK = [("Pay", (40, 300, 110, 320)), ("Done", (40, 400, 110, 420))]


class Frame:
    def __init__(self, url: str) -> None:
        self.url = url


class FakePage:
    def __init__(self) -> None:
        self.main_frame = Frame("")
        self.handlers: list[tuple[str, object]] = []
        self.url = "https://parabank.parasoft.com/parabank/x.htm"
        self.calls: list[str] = []

    def on(self, event: str, fn: object) -> None:
        self.handlers.append((event, fn))

    def remove_listener(self, event: str, fn: object) -> None:
        self.handlers.remove((event, fn))

    async def screenshot(self) -> bytes:
        return b"shot"


class Req:
    def __init__(self, method: str, url: str, body: str = "amount=10") -> None:
        self.method, self.url, self.post_data = method, url, body


class Route:
    def __init__(self, method: str, url: str) -> None:
        self.request = Req(method, url)

    async def continue_(self, **_: object) -> None:
        return None

    async def abort(self) -> None:
        return None


def _env(page: object | None = None, **cfg: float) -> Ctx:
    ctx = make_replay_ctx(page or FakePage(), cfg=ReplayConfig(**cfg))  # type: ignore[arg-type]
    screen(ctx, mk_look(LOOK, png=b"shot"))
    return ctx


class HumanControl:
    """Takes over; while 'in control', the human opens a page and sends a form."""

    def __init__(self, ctx: Ctx) -> None:
        self.ctx = ctx

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        if mode == "rescue":
            return "takeover"
        page = self.ctx.page
        for _event, fn in list(page.handlers):  # type: ignore[attr-defined]
            fn(Frame("https://x/other"))  # an iframe: ignored
        page.main_frame.url = (
            "https://parabank.parasoft.com/parabank/billpay.htm;jsessionid=AB12?payee=Sean"
        )
        for _event, fn in list(page.handlers):  # type: ignore[attr-defined]
            fn(page.main_frame)
        self.ctx.run.allow_send = True
        await self.ctx.guard(Route("POST", "https://parabank.parasoft.com/parabank/services/pay?amount=10"))  # type: ignore[arg-type]
        await self.ctx.guard(Route("GET", "https://parabank.parasoft.com/parabank/overview.htm"))  # type: ignore[arg-type]
        self.ctx.run.allow_send = False
        return "done"


def _fail_clicks(mp: pytest.MonkeyPatch) -> None:
    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        return False

    mp.setitem(steps.ACTIONS, "click", clicked)


@pytest.mark.asyncio
async def test_take_over_marks_the_result_with_step_and_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _env()
    set_control(ctx, HumanControl(ctx))
    _fail_clicks(monkeypatch)
    res = await engine.walk(ctx, cap([click("Pay"), click("Pay")]), None, [])
    assert res.status == "SUCCESS"
    assert res.human[0] == {
        "step": 0,
        "reason": "the step's check failed",
        "actions": {"pages": ["/parabank/billpay.htm"], "sends": ["/parabank/services/pay"]},
    }
    assert [h["step"] for h in res.human] == [0, 1]
    assert res.summary == "SUCCESS (human intervened at steps 1, 2)"
    entry = next(d for d in res.drift if d["rung"] == "human")
    assert entry["shots"] == {"start": b"shot", "end": b"shot"}
    assert ctx.page.handlers == [] and ctx.run.takeover is None  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_no_take_over_means_an_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _env()

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        return True

    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    res = await engine.walk(ctx, cap([click("Pay")]), None, [])
    assert res.status == "SUCCESS" and res.human == [] and res.summary == "SUCCESS"


@pytest.mark.asyncio
async def test_no_values_in_the_take_over_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _env()
    set_control(ctx, HumanControl(ctx))
    _fail_clicks(monkeypatch)
    res = await engine.walk(ctx, cap([click("Pay")]), None, [])
    entry = {
        k: v for k, v in next(d for d in res.drift if d["rung"] == "human").items() if k != "shots"
    }
    text = repr(entry)
    assert (
        "Sean" not in text
        and "amount" not in text
        and "10" not in text
        and "jsessionid" not in text
    )


@pytest.mark.asyncio
async def test_sends_are_noted_only_during_a_take_over() -> None:
    ctx = _env()
    ctx.run.allow_send = True
    await ctx.guard(Route("POST", "https://parabank.parasoft.com/parabank/services/pay"))  # type: ignore[arg-type]
    assert ctx.run.takeover is None


@pytest.mark.asyncio
async def test_the_gate_marks_a_human_approved_send() -> None:
    ctx = _env()
    ctx.run.allow_send = True  # the login click: exempt, not a gated send
    await ctx.guard(Route("POST", "https://parabank.parasoft.com/x"))  # type: ignore[arg-type]
    assert ctx.run.gated is False and ctx.run.sent is True


class HeldPage(FakePage):
    """Like Playwright: while a form POST (a navigation) is held, `page.screenshot()` never returns."""

    def __init__(self) -> None:
        super().__init__()
        self.held, self.shots = False, 0

    async def screenshot(self) -> bytes:
        self.shots += 1
        while self.held:
            await asyncio.sleep(0.01)
        return b"shot"


def _real_shots(ctx: Ctx) -> None:
    """take_look screenshots the page, as the real one does."""
    lk = ctx.run.look

    async def shoot() -> Look:
        await ctx.page.screenshot()
        return lk  # type: ignore[return-value]

    ctx.shoot = shoot


class HeldRoute(Route):
    def __init__(self, page: HeldPage) -> None:
        super().__init__("POST", "https://parabank.parasoft.com/parabank/billpay.htm")
        self.page, self.done = page, ""
        page.held = True

    async def continue_(self, **_: object) -> None:
        self.page.held, self.done = False, "sent"

    async def abort(self) -> None:
        self.page.held, self.done = False, "aborted"


class GateControl:
    def __init__(self) -> None:
        self.asked: list[str] = []

    async def ask(
        self, title: str, details: str, mode: str, image: bytes | None = None, **_: object
    ) -> str:
        self.asked.append(mode)
        await asyncio.sleep(0)
        return "approve"


@pytest.mark.asyncio
async def test_navigation_send_never_screenshots_and_the_gate_shows() -> None:
    ctx = _env(HeldPage())
    _real_shots(ctx)
    set_control(ctx, ctl := GateControl())
    ctx.run.given = ["10"]
    route = HeldRoute(ctx.page)  # type: ignore[arg-type]
    await asyncio.wait_for(ctx.guard(route), 1)  # type: ignore[arg-type]
    assert ctl.asked == ["confirm", "approve"] and route.done == "sent"
    assert ctx.page.shots == 0  # type: ignore[attr-defined]


class HumanSimple:
    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        return "takeover" if mode == "rescue" else "done"


@pytest.mark.asyncio
async def test_take_over_survives_a_screenshot_timeout() -> None:
    ctx = _env(HeldPage(), snap_s=0.05)
    _real_shots(ctx)
    set_control(ctx, HumanSimple())
    ctx.page.held = True  # type: ignore[attr-defined]
    evidence = await asyncio.wait_for(rescue.rescue(ctx, 0, click("Pay"), "why"), 2)
    assert evidence["shots"] == {"start": None, "end": None}
    assert ctx.run.human[0]["step"] == 0


class DoneWhileSending:
    """The human clicks Done just as their form POST is held: the gate must still show and finish."""

    def __init__(self, ctx: Ctx) -> None:
        self.ctx, self.asked = ctx, []
        self.task: asyncio.Task[None] | None = None

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        self.asked.append(mode)
        if mode == "rescue":
            return "takeover"
        if mode == "takeover":
            self.task = asyncio.create_task(self.ctx.guard(HeldRoute(self.ctx.page)))  # type: ignore[arg-type]
            await asyncio.sleep(0)  # the guard takes the gate first
            return "done"
        await asyncio.sleep(0.02)
        return "approve"


@pytest.mark.asyncio
async def test_no_deadlock_between_a_pending_gate_and_done() -> None:
    ctx = _env(HeldPage())
    _real_shots(ctx)
    ctx.run.given = ["10"]
    set_control(ctx, ctl := DoneWhileSending(ctx))
    evidence = await asyncio.wait_for(rescue.rescue(ctx, 0, click("Pay"), "why"), 2)
    assert (
        ctl.asked == ["rescue", "takeover", "confirm", "approve"] and ctl.task and ctl.task.done()
    )
    assert evidence["shots"]["end"] == b"shot"  # type: ignore[index]
    assert evidence["actions"]["sends"] == ["/parabank/billpay.htm"]  # type: ignore[index]


class HangPage(HeldPage):
    """`evaluate` also never returns while a request is held, as live."""

    def __init__(self, dropdowns: list[dict[str, object]] | None = None) -> None:
        super().__init__()
        self.evals, self.dropdowns = 0, list(dropdowns or [])

    async def evaluate(self, js: str, *args: object) -> list[dict[str, object]]:
        self.evals += 1
        while self.held:
            await asyncio.sleep(0.01)
        return [dict(d) for d in self.dropdowns]


class FormRoute(HeldRoute):
    def __init__(self, page: HeldPage, body: str = "fromAccountId=13344&amount=10") -> None:
        super().__init__(page)
        self.request.post_data, self.sent_body = body, None

    async def continue_(
        self, url: str | None = None, post_data: str | None = None, **_: object
    ) -> None:
        self.page.held, self.done, self.sent_body = False, "sent", post_data


class ScriptedControl:
    """Answers each gate from a script; records what each form offered."""

    def __init__(self, answers: list[object]) -> None:
        self.answers, self.asked, self.forms = list(answers), [], []

    async def ask(self, title: str, details: str, mode: str, **_: object) -> object:
        self.asked.append(mode)
        return self.answers.pop(0)

    async def form(
        self, title: str, fields: object, values: object = None, options: object = None
    ) -> object:
        self.forms.append(options)
        return self.answers.pop(0)


STASH = [{"value": "13344", "text": "13344", "options": ["13344", "74838"]}]


@pytest.mark.asyncio
async def test_human_post_during_a_take_over_passes_both_gates_with_no_evaluate() -> None:
    ctx = _env(HangPage(STASH))
    _real_shots(ctx)
    ctx.run.takeover = {"pages": [], "sends": []}
    set_control(ctx, ctl := ScriptedControl(["edit", ["74838", "20"], "approve", "approve"]))
    route = FormRoute(ctx.page)  # type: ignore[arg-type]
    await asyncio.wait_for(ctx.guard(route), 1)  # type: ignore[arg-type]
    assert ctl.asked == ["confirm", "confirm", "approve"]  # no mismatch form first
    assert ctl.forms == [None]  # Edit = plain text fields
    assert route.done == "sent" and "74838" in (route.sent_body or "")
    assert ctx.page.evals == 0 and ctx.page.shots == 0  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_agent_send_uses_the_stash_not_the_page() -> None:
    ctx = _env(HangPage())
    _real_shots(ctx)
    ctx.run.dropdowns = [dict(d) for d in STASH]
    set_control(ctx, ctl := ScriptedControl([["13344", "10"], "approve", "approve"]))
    route = FormRoute(ctx.page)  # type: ignore[arg-type]
    await asyncio.wait_for(ctx.guard(route), 1)  # type: ignore[arg-type]
    assert ctl.forms[0] == [["13344", "74838"], []] and route.done == "sent"
    assert ctx.page.evals == 0  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_click_stashes_the_dropdowns_before_clicking(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _env(HangPage([{"value": "1", "text": "1", "options": ["1", "2"]}]))
    order: list[object] = []

    async def act(c: Ctx, *s: object) -> Look:
        order.append(("click", list(c.run.dropdowns)))
        return c.run.look  # type: ignore[return-value]

    async def settled(c: Ctx, before: Look) -> bool:
        return True

    monkeypatch.setattr(steps, "act", act)
    monkeypatch.setattr(steps, "settled_change", settled)
    await steps.do_click(ctx, click("Pay"), (75, 310), None)  # type: ignore[arg-type]
    assert order == [("click", [{"value": "1", "text": "1", "options": ["1", "2"]}])]


@pytest.mark.asyncio
async def test_stash_read_on_a_held_page_times_out_to_empty() -> None:
    ctx = _env(HangPage([{"value": "1", "text": "1", "options": ["1", "2"]}]), page_s=0.05)
    ctx.page.held = True  # type: ignore[attr-defined]
    assert await asyncio.wait_for(stash_dropdowns(ctx), 1) == []
    assert DROPDOWNS_JS  # the replay side's own (values-only) script


class NeverAnsweredGate:
    """The human clicks Done while their own send's Gate 1 is still open and never answered."""

    def __init__(self, ctx: Ctx) -> None:
        self.ctx = ctx
        self.task: asyncio.Task[None] | None = None

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        if mode == "rescue":
            return "takeover"
        if mode == "takeover":
            self.task = asyncio.create_task(self.ctx.guard(FormRoute(self.ctx.page)))  # type: ignore[arg-type]
            await asyncio.sleep(0)
            return "done"
        await asyncio.Event().wait()  # the gate is never answered
        return ""


@pytest.mark.asyncio
async def test_done_hands_back_within_a_timeout_as_stuck() -> None:
    ctx = _env(HangPage(), snap_s=0.05, gate_s=0.1)
    _real_shots(ctx)
    set_control(ctx, ctl := NeverAnsweredGate(ctx))
    try:
        with pytest.raises(Stop) as e:
            await asyncio.wait_for(rescue.rescue(ctx, 0, click("Pay"), "why"), 2)
    finally:
        assert ctl.task is not None
        ctl.task.cancel()
    assert e.value.status == "STUCK" and "send" in e.value.reason
    assert ctx.run.human[0]["actions"]["sends"] == ["/parabank/billpay.htm"]  # type: ignore[index]


@pytest.mark.asyncio
async def test_checkpoint_reached_by_the_human_skips_the_remaining_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live: the human finished the whole form during a take-over; step 6 then 'target not found'."""
    ctx = _env()
    done = Look(b"shot", b"shot", (Element(1, "Bill Payment Complete", Box(0, 0, 90, 10)),), "")

    class Finishes:
        async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
            if mode == "rescue":
                return "takeover"
            ctx.run.look = done
            return "done"

    async def shoot() -> Look:
        return ctx.run.look  # type: ignore[return-value]

    ctx.shoot = shoot
    set_control(ctx, Finishes())
    tried: list[str] = []

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        tried.append(step.target.ocr_text.text)  # type: ignore[union-attr]
        return False

    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    res = await engine.walk(
        ctx,
        cap([click("Pay"), click("City"), click("Send")], checkpoint="Bill Payment Complete"),
        None,
        [],
    )
    assert res.status == "SUCCESS" and tried == ["Pay", "Pay"]
    assert [d for d in res.drift if d.get("rung") == "skipped"] == [
        {"step": 1, "action": "click", "rung": "skipped"},
        {"step": 2, "action": "click", "rung": "skipped"},
    ]


def _human_lands_on(ctx: Ctx, text: str) -> None:
    """A take-over that ends on a screen showing `text` (the checkpoint)."""
    landed = Look(b"shot", b"shot", (Element(1, text, Box(0, 0, 90, 10)),), "")

    class Lands:
        async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
            if mode == "rescue":
                return "takeover"
            ctx.run.look = landed
            return "done"

    async def shoot() -> Look:
        return ctx.run.look  # type: ignore[return-value]

    ctx.shoot = shoot
    set_control(ctx, Lands())


@pytest.mark.asyncio
async def test_read_steps_still_run_after_the_human_reaches_the_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live (takeover_demo): the human landed on Bill Pay ('City:'); the extract_options step
    that reads the output was skipped, so the run FAILED with the output missing."""
    ctx = _env()
    _human_lands_on(ctx, "City:")
    tried: list[str] = []

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        tried.append(step.target.ocr_text.text)  # type: ignore[union-attr]
        return step.target.ocr_text.text == "Log Out"  # type: ignore[union-attr]

    async def read(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        c.run.outputs[step.save_as] = "12345"  # type: ignore[union-attr]
        return True

    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    monkeypatch.setitem(steps.ACTIONS, "extract", read)
    res = await engine.walk(
        ctx,
        cap(
            [
                click("Pay"),
                extract(
                    "account",
                    {"ocr_text": {"text": "City:"}, "anchor": {"label": "City:", "offset": [0, 0]}},
                ),
                click("Log Out", cleanup=True),
            ],
            checkpoint="City:",
            outputs=[{"name": "account", "type": "text", "description": "a"}],
        ),
        None,
        [],
    )
    assert res.status == "SUCCESS" and res.outputs == {"account": "12345"}
    assert res.human and res.human[0]["step"] == 0
    assert not [d for d in res.drift if d.get("rung") == "skipped"]


@pytest.mark.asyncio
async def test_acting_steps_after_the_checkpoint_take_over_stay_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only reads run after the human reached the checkpoint: a click or a type is skipped."""
    ctx = _env()
    _human_lands_on(ctx, "City:")
    acted: list[str] = []

    async def acts(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        acted.append(step.action)
        return False

    async def read(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        c.run.outputs[step.save_as] = "12345"  # type: ignore[union-attr]
        return True

    monkeypatch.setitem(steps.ACTIONS, "click", acts)
    monkeypatch.setitem(steps.ACTIONS, "type", acts)
    monkeypatch.setitem(steps.ACTIONS, "extract", read)
    res = await engine.walk(
        ctx,
        cap(
            [
                click("Pay"),
                type_("x", label="City:"),
                extract(
                    "account",
                    {"ocr_text": {"text": "City:"}, "anchor": {"label": "City:", "offset": [0, 0]}},
                ),
                click("Send"),
            ],
            checkpoint="City:",
            outputs=[{"name": "account", "type": "text", "description": "a"}],
        ),
        None,
        [],
    )
    assert res.status == "SUCCESS" and acted == ["click", "click"]  # only step 0's two tries
    assert [d for d in res.drift if d.get("rung") == "skipped"] == [
        {"step": 1, "action": "type", "rung": "skipped"},
        {"step": 3, "action": "click", "rung": "skipped"},
    ]

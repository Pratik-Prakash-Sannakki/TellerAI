"""The step loop on fakes: success, one retry, never re-send, stuck on a miss (R17 taxonomy,
cleanup, partial outputs). Ported from tests/replay/test_engine.py, test_outcomes.py,
test_cleanup.py and test_partial_outputs.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from cua.config import ReplayConfig
from cua.replay import engine, loader, steps
from cua.replay.context import Ctx
from cua.schema import Capability, ReplayResult, Step, Stop
from cua.vision import Look
from tests.unit.replay.helpers import (
    cap,
    click,
    extract,
    make_replay_ctx,
    mk_look,
    navigate,
    screen,
    set_control,
    type_,
    write_cap,
)


class AskStop:
    def __init__(self) -> None:
        self.asked: list[str] = []

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        self.asked.append(mode)
        return "stop"


def script(
    mp: pytest.MonkeyPatch, ctx: Ctx, action: str, results: list[bool], send: bool = False
) -> list[object]:
    calls: list[object] = []

    async def fake(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        calls.append(point)
        c.run.sent = send
        return results[len(calls) - 1]

    mp.setitem(steps.ACTIONS, action, fake)
    return calls


async def walk(ctx: Ctx, cp: Capability) -> ReplayResult | Stop:
    try:
        return await engine.walk(ctx, cp, None, [])
    except Stop as s:
        return s


# --- the loop (test_engine.py) -------------------------------------------------------------

LOGIN = [("Username", (40, 100, 100, 120)), ("Transfer", (40, 300, 110, 320))]


@pytest.fixture
def ectx() -> Ctx:
    ctx = make_replay_ctx(control=AskStop())
    screen(ctx, mk_look(LOGIN))
    return ctx


@pytest.mark.asyncio
async def test_success_with_drift(ectx: Ctx, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = script(monkeypatch, ectx, "click", [True])
    res = await walk(ectx, cap([click("Transfer")], checkpoint="Transfer"))
    assert isinstance(res, ReplayResult)
    assert res.status == "SUCCESS" and calls == [(75, 310)]
    assert res.drift == [
        {
            "step": 0,
            "action": "click",
            "rung": "rung1",
            "point": (75, 310),
            "attempt": 1,
            "checked": True,
        }
    ]


@pytest.mark.asyncio
async def test_failed_check_retried_once(ectx: Ctx, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = script(monkeypatch, ectx, "type", [False, True])
    ectx.run.values = {"x": "v"}
    res = await walk(ectx, cap([type_("{{x}}")], checkpoint="Transfer"))
    assert res.status == "SUCCESS" and len(calls) == 2


@pytest.mark.asyncio
async def test_send_never_retried(ectx: Ctx, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = script(monkeypatch, ectx, "click", [False, True], send=True)
    res = await walk(ectx, cap([click("Transfer")], checkpoint="Transfer"))
    assert res.status == "STUCK" and len(calls) == 1 and ectx.control.asked == ["rescue"]  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_secret_never_retried(ectx: Ctx, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = script(monkeypatch, ectx, "type", [False, True])
    res = await walk(ectx, cap([type_("{{secret:password}}")], checkpoint="Transfer"))
    assert res.status == "STUCK" and len(calls) == 1


@pytest.mark.asyncio
async def test_locate_miss_is_stuck(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = make_replay_ctx(control=AskStop(), cfg=ReplayConfig(scroll_retries=0))
    screen(ctx, mk_look(LOGIN))
    calls = script(monkeypatch, ctx, "click", [True])
    res = await walk(ctx, cap([click("Bill Pay")], checkpoint="Transfer"))
    assert isinstance(res, Stop)
    assert res.status == "STUCK" and res.reason == "target not found" and calls == []


@pytest.mark.asyncio
async def test_gate2_reject_is_declined(ectx: Ctx, monkeypatch: pytest.MonkeyPatch) -> None:
    async def declined(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        c.run.verdict = "DECLINED: a human said no at Gate 2. Nothing was sent."
        return False

    monkeypatch.setitem(steps.ACTIONS, "click", declined)
    assert (await walk(ectx, cap([click("Transfer")], checkpoint="Transfer"))).status == "DECLINED"


# --- R17 outcomes (test_outcomes.py) -------------------------------------------------------

OUT_LOGIN = [("Username", (40, 100, 110, 120)), ("LOG IN", (40, 160, 100, 180))]
HOME = [("Welcome", (40, 40, 140, 60)), ("Pay", (40, 300, 80, 320))]
SCREENS = {
    "login": OUT_LOGIN,
    "home": HOME,
    "expired": [("Your session expired", (40, 40, 240, 60)), *OUT_LOGIN],
    "done": [("Done", (40, 40, 90, 60))],
    "missing": [("Account not found", (40, 40, 240, 60))],
    "error": [("Error!", (40, 40, 100, 60)), ("An internal error occurred", (40, 70, 300, 90))],
}


@pytest.fixture
def site(monkeypatch: pytest.MonkeyPatch) -> tuple[Ctx, dict[str, object]]:
    looks = {k: mk_look(v) for k, v in SCREENS.items()}
    state: dict[str, object] = {"now": "login", "pay": []}
    ctx = make_replay_ctx(cfg=ReplayConfig(check_s=0))

    async def shoot() -> Look:
        return looks[state["now"]]  # type: ignore[index]

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        if step.target.ocr_text.text == "LOG IN":  # type: ignore[union-attr]
            state["now"] = "home"
        else:
            state["now"] = state["pay"].pop(0)  # type: ignore[attr-defined]
        c.run.look = await c.shoot()
        return True

    async def typed(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        return True

    ctx.shoot = shoot
    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    monkeypatch.setitem(steps.ACTIONS, "type", typed)
    ctx.run.look = looks["login"]
    ctx.run.outcomes = [
        {"text": o.text, "status": o.status, "meaning": o.meaning} for o in ctx.site.outcomes
    ]
    return ctx, state


def _login_cap() -> Capability:
    return cap([type_("{{secret:username}}"), click("LOG IN"), click("Pay")])


@pytest.mark.asyncio
async def test_not_found_screen_is_a_business_outcome_with_its_meaning(
    site: tuple[Ctx, dict[str, object]],
) -> None:
    ctx, state = site
    state["pay"] = ["missing"]
    with pytest.raises(Stop) as e:
        await engine.walk(ctx, _login_cap(), None, [])
    meaning = next(o.meaning for o in ctx.site.outcomes if o.text == "not found")
    assert e.value.status == "BUSINESS_OUTCOME" and e.value.reason == meaning
    assert e.value.observed.startswith("Account not found")


@pytest.mark.asyncio
async def test_expired_session_is_recovered_once(site: tuple[Ctx, dict[str, object]]) -> None:
    ctx, state = site
    state["pay"] = ["expired", "done"]
    res = await engine.walk(ctx, _login_cap(), None, [])
    assert res.status == "SUCCESS" and res.recoveries == 1


@pytest.mark.asyncio
async def test_a_second_expiry_is_not_recovered_again(site: tuple[Ctx, dict[str, object]]) -> None:
    ctx, state = site
    state["pay"] = ["expired", "expired"]
    with pytest.raises(Stop) as e:
        await engine.walk(ctx, _login_cap(), None, [])
    assert e.value.status == "FAILED" and ctx.run.recoveries == 1


@pytest.mark.asyncio
async def test_error_page_fails_with_detail(site: tuple[Ctx, dict[str, object]]) -> None:
    ctx, state = site
    state["pay"] = ["error"]
    with pytest.raises(Stop) as e:
        await engine.walk(ctx, _login_cap(), None, [])
    assert e.value.status == "FAILED" and ctx.run.step == 2
    assert e.value.expected == "step 3 without 'error'"
    assert e.value.observed == "Error! An internal error occurred"


@pytest.mark.asyncio
async def test_a_send_is_never_retried_after_an_expiry(
    site: tuple[Ctx, dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, state = site
    state["pay"] = ["expired", "done"]
    clicked = steps.ACTIONS["click"]

    async def sending(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        c.run.sent = step.target.ocr_text.text == "Pay"  # type: ignore[union-attr]
        return await clicked(c, step, point, cp)

    monkeypatch.setitem(steps.ACTIONS, "click", sending)
    with pytest.raises(Stop) as e:
        await engine.walk(ctx, _login_cap(), None, [])
    assert e.value.status == "FAILED" and ctx.run.recoveries == 0


@pytest.mark.asyncio
async def test_login_page_back_mid_run_is_recovered(site: tuple[Ctx, dict[str, object]]) -> None:
    ctx, state = site
    state["pay"] = ["login", "done"]
    res = await engine.walk(ctx, _login_cap(), None, [])
    assert res.status == "SUCCESS" and res.recoveries == 1


# --- cleanup (test_cleanup.py) -------------------------------------------------------------

CLEAN = [
    ("Username", (40, 100, 110, 120)),
    ("Pay", (40, 300, 80, 320)),
    ("Log Out", (40, 20, 100, 40)),
    ("Done", (40, 400, 90, 420)),
]


@pytest.fixture
def clean(monkeypatch: pytest.MonkeyPatch) -> tuple[Ctx, list[str], set[str]]:
    ctx = make_replay_ctx()
    screen(ctx, mk_look(CLEAN))
    order: list[str] = []
    fails: set[str] = set()

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        order.append(step.target.ocr_text.text)  # type: ignore[union-attr]
        if step.target.ocr_text.text in fails:  # type: ignore[union-attr]
            raise Stop("FAILED", "the click left the allowed site")
        return True

    async def shows(c: Ctx, text: str) -> bool:
        order.append(f"checkpoint:{text}")
        return text == "Done"

    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    monkeypatch.setattr(steps, "shows", shows)
    return ctx, order, fails


async def _finish(ctx: Ctx, cp: Capability) -> ReplayResult:
    return await engine.finish(ctx, cp, None, [])


@pytest.mark.asyncio
async def test_success_then_cleanup_in_order_after_the_checkpoint(
    clean: tuple[Ctx, list[str], set[str]],
) -> None:
    ctx, order, _ = clean
    res = await _finish(ctx, cap([click("Pay"), click("Log Out", cleanup=True)]))
    assert order == ["Pay", "checkpoint:Done", "Log Out"]
    assert res.status == "SUCCESS" and res.cleanup == "done"
    assert res.drift[-1]["cleanup"] is True and res.drift[-1]["action"] == "click"


@pytest.mark.asyncio
async def test_cleanup_runs_after_a_failed_step(
    clean: tuple[Ctx, list[str], set[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, order, fails = clean
    fails.add("Pay")
    monkeypatch.setattr(engine, "snap", _no_snap)
    res = await _finish(ctx, cap([click("Pay"), click("Log Out", cleanup=True)]))
    assert order == ["Pay", "Log Out"] and res.status == "FAILED" and res.cleanup == "done"


async def _no_snap(ctx: Ctx) -> None:
    return None


@pytest.mark.asyncio
async def test_cleanup_runs_after_a_failed_checkpoint(
    clean: tuple[Ctx, list[str], set[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, order, _ = clean
    monkeypatch.setattr(engine, "snap", _no_snap)
    res = await _finish(ctx, cap([click("Pay"), click("Log Out", cleanup=True)], checkpoint="Nope"))
    assert order[-1] == "Log Out" and res.status == "FAILED" and res.cleanup == "done"


@pytest.mark.asyncio
async def test_a_cleanup_failure_keeps_success_and_records_failed(
    clean: tuple[Ctx, list[str], set[str]],
) -> None:
    ctx, order, fails = clean
    fails.add("Log Out")
    res = await _finish(ctx, cap([click("Pay"), click("Log Out", cleanup=True)]))
    assert res.status == "SUCCESS" and res.cleanup == "failed: the click left the allowed site"
    assert order.count("Log Out") == 1


@pytest.mark.asyncio
async def test_a_cleanup_miss_is_retried_once_then_recorded_without_a_rescue(
    clean: tuple[Ctx, list[str], set[str]],
) -> None:
    ctx, _, _ = clean
    ctx.cfg = ReplayConfig(scroll_retries=0)
    set_control(ctx, ctl := AskStop())
    res = await _finish(ctx, cap([click("Pay"), click("Sign off", cleanup=True)]))
    assert res.status == "SUCCESS" and res.cleanup == "failed: target not found" and ctl.asked == []


@pytest.mark.asyncio
async def test_old_artifacts_without_cleanup_are_unchanged(
    clean: tuple[Ctx, list[str], set[str]],
) -> None:
    ctx, order, _ = clean
    res = await _finish(ctx, cap([click("Pay")]))
    assert order == ["Pay", "checkpoint:Done"] and res.status == "SUCCESS" and res.cleanup == ""
    assert all("cleanup" not in d for d in res.drift)


@pytest.mark.asyncio
async def test_no_cleanup_when_stopped_before_step_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-secret")
    ran: list[str] = []
    ctx = make_replay_ctx()

    async def open_start(c: Ctx, cp: Capability) -> None:
        ran.append("open")

    async def ask_inputs(c: Ctx, cp: Capability, given: dict[str, str]) -> dict[str, str]:
        raise Stop("STUCK", "inputs not given: ['x']")

    async def cleanup(*a: object) -> str:
        ran.append("cleanup")
        return "done"

    monkeypatch.setattr(engine, "open_start", open_start)
    monkeypatch.setattr(loader, "ask_inputs", ask_inputs)
    monkeypatch.setattr(engine, "snap", _no_snap)
    monkeypatch.setattr(engine, "run_cleanup", cleanup)
    res = await engine.replay(ctx, write_cap(tmp_path))
    assert res.status == "STUCK" and ran == ["open"] and res.cleanup == ""


# --- partial outputs (test_partial_outputs.py) ---------------------------------------------

PARTIAL = [
    ("Balance", (40, 300, 120, 320)),
    ("$515.50", (200, 300, 260, 320)),
    ("Pay", (40, 400, 80, 420)),
]
BALANCE = {"anchor": {"label": "Balance", "offset": [150, 0]}}


@pytest.fixture
def pctx(monkeypatch: pytest.MonkeyPatch) -> Ctx:
    ctx = make_replay_ctx(control=AskStop(), cfg=ReplayConfig(check_s=0, scroll_retries=0))
    screen(ctx, mk_look(PARTIAL))

    async def clicked(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        return True

    monkeypatch.setitem(steps.ACTIONS, "click", clicked)
    monkeypatch.setattr(engine, "snap", _no_snap)
    return ctx


def _pcap(
    steps_: list[object], outputs: list[str], checkpoint: str = "Customer Login"
) -> Capability:
    return cap(
        steps_,
        checkpoint,
        outputs=[{"name": n, "type": "currency", "description": n} for n in outputs],
    )


@pytest.mark.asyncio
async def test_a_failed_run_still_returns_what_it_read(pctx: Ctx) -> None:
    cp = _pcap(
        [extract("balance", BALANCE), click("Nowhere")], ["balance", "other"], checkpoint="Done"
    )
    res = await _finish(pctx, cp)
    assert res.status != "SUCCESS" and res.outputs == {"balance": "$515.50"}


@pytest.mark.asyncio
async def test_missing_outputs_are_named_in_the_reason(pctx: Ctx) -> None:
    res = await _finish(
        pctx, _pcap([extract("balance", BALANCE)], ["balance", "available"], checkpoint="Pay")
    )
    assert res.status == "FAILED" and res.reason == "outputs not read: ['available']"
    assert res.outputs == {"balance": "$515.50"}


def test_partial_label_when_not_success() -> None:
    assert (
        ReplayResult("FAILED", {"b": "1"}, []).outputs_line
        == "partial outputs (run did not succeed): {'b': '1'}"
    )
    assert ReplayResult("SUCCESS", {"b": "1"}, []).outputs_line == "outputs: {'b': '1'}"


@pytest.mark.asyncio
async def test_read_only_run_with_a_login_page_checkpoint_is_success(pctx: Ctx) -> None:
    res = await _finish(pctx, _pcap([click("Pay"), extract("balance", BALANCE)], ["balance"]))
    assert res.status == "SUCCESS" and res.outputs == {"balance": "$515.50"}
    assert res.reason == "checkpoint looked for after cleanup; all outputs read"


@pytest.mark.asyncio
async def test_a_run_with_a_send_is_not_rescued_this_way(
    pctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def sending(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        c.run.gated = True  # a send went through the human gates
        return True

    monkeypatch.setitem(steps.ACTIONS, "click", sending)
    res = await _finish(pctx, _pcap([click("Pay"), extract("balance", BALANCE)], ["balance"]))
    assert res.status == "FAILED" and res.reason == "checkpoint text not on the final screen"
    assert res.outputs == {"balance": "$515.50"}


@pytest.mark.asyncio
async def test_not_rescued_when_the_last_main_step_is_not_an_extract(pctx: Ctx) -> None:
    res = await _finish(pctx, _pcap([extract("balance", BALANCE), click("Pay")], ["balance"]))
    assert res.status == "FAILED"


@pytest.mark.asyncio
async def test_checkpoint_miss_carries_expected_and_observed() -> None:
    """From test_replay_evidence.py: a checkpoint miss is FAILED after the last step."""
    lk = mk_look([("Error", (0, 0, 40, 10)), ("x" * 300, (0, 20, 40, 30))])
    ctx = make_replay_ctx(cfg=ReplayConfig(check_s=0))
    screen(ctx, lk)

    async def nav(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
        return True

    mp = pytest.MonkeyPatch()
    mp.setitem(steps.ACTIONS, "navigate", nav)
    try:
        with pytest.raises(Stop) as e:
            await engine.walk(ctx, cap([navigate("/x")], checkpoint="Transfer Complete!"), None, [])
    finally:
        mp.undo()
    assert e.value.expected == "Transfer Complete!" and e.value.observed == lk.text[:200]
    assert ctx.run.step == 1 and ctx.run.action == "checkpoint"

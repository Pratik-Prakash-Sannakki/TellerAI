"""Cleanup steps (e.g. Log Out) run last, always, best-effort, and never change the main status."""
import asyncio

import pytest

from test_load_inputs import CAP, _write

SCREEN = [("Username", (40, 100, 110, 120)), ("Pay", (40, 300, 80, 320)), ("Log Out", (40, 20, 100, 40)),
          ("Done", (40, 400, 90, 420))]


def _click(ns, text, cleanup=False):
    step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}})
    return step.model_copy(update={"cleanup": True}) if cleanup else step   # works before discovery's field lands


@pytest.fixture
def site(ns, mk_look):
    lk = mk_look(SCREEN)
    order: list[str] = []
    fails: set[str] = set()

    async def take_look():
        ns["STATE"].look = lk
        return lk

    async def click(step, point, cap):
        order.append(step.target.ocr_text.text)
        if step.target.ocr_text.text in fails:
            raise ns["Stop"]("FAILED", "the click left the allowed site")
        return True

    async def shows(text):
        order.append(f"checkpoint:{text}")
        return text == "Done"

    ns.update(take_look=take_look, shows=shows)
    ns["ACTIONS"] = {**ns["ACTIONS"], "click": click}
    ns["STATE"].look = lk
    return ns, order, fails


def _cap(ns, steps, checkpoint="Done"):
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=steps, checkpoint=checkpoint)


def _run(ns, cap):
    return asyncio.run(ns["finish"](cap, None, []))


def test_success_then_cleanup_in_order_after_the_checkpoint(site) -> None:
    ns, order, _ = site
    cap = _cap(ns, [_click(ns, "Pay"), _click(ns, "Log Out", cleanup=True)])
    res = _run(ns, cap)
    assert order == ["Pay", "checkpoint:Done", "Log Out"]
    assert res.status == "SUCCESS" and res.cleanup == "done"
    assert res.drift[-1]["cleanup"] is True and res.drift[-1]["action"] == "click"


def test_cleanup_runs_after_a_failed_step(site) -> None:
    ns, order, fails = site
    fails.add("Pay")
    cap = _cap(ns, [_click(ns, "Pay"), _click(ns, "Log Out", cleanup=True)])
    res = _run(ns, cap)
    assert order == ["Pay", "Log Out"] and res.status == "FAILED" and res.cleanup == "done"


def test_cleanup_runs_after_a_failed_checkpoint(site) -> None:
    ns, order, _ = site
    cap = _cap(ns, [_click(ns, "Pay"), _click(ns, "Log Out", cleanup=True)], checkpoint="Nope")
    res = _run(ns, cap)
    assert order[-1] == "Log Out" and res.status == "FAILED" and res.cleanup == "done"


def test_a_cleanup_failure_keeps_success_and_records_failed(site) -> None:
    ns, order, fails = site
    fails.add("Log Out")
    cap = _cap(ns, [_click(ns, "Pay"), _click(ns, "Log Out", cleanup=True)])
    res = _run(ns, cap)
    assert res.status == "SUCCESS" and res.cleanup == "failed: the click left the allowed site"
    assert order.count("Log Out") == 1                                # no rescue, no retry of a raised step


def test_a_cleanup_miss_is_retried_once_then_recorded_without_a_rescue(site) -> None:
    ns, order, _ = site
    asked = []

    class Control:
        async def ask(self, *a, **k):
            asked.append(a)
            return "stop"

    ns["CONTROL"] = Control()
    ns["CFG"] = ns["Config"](scroll_retries=0)
    cap = _cap(ns, [_click(ns, "Pay"), _click(ns, "Sign off", cleanup=True)])
    res = _run(ns, cap)
    assert res.status == "SUCCESS" and res.cleanup == "failed: target not found" and asked == []


def test_old_artifacts_without_cleanup_are_unchanged(site) -> None:
    ns, order, _ = site
    res = _run(ns, _cap(ns, [_click(ns, "Pay")]))
    assert order == ["Pay", "checkpoint:Done"] and res.status == "SUCCESS" and res.cleanup == ""
    assert all("cleanup" not in d for d in res.drift)


def test_no_cleanup_when_stopped_before_step_1(ns, tmp_path) -> None:
    ran = []

    async def open_start(cap):
        ran.append("open")

    async def ask_inputs(cap, given):
        raise ns["Stop"]("STUCK", "inputs not given: ['x']")

    async def snap():
        return None

    async def cleanup(*a):
        ran.append("cleanup")
        return "done"

    ns.update(open_start=open_start, ask_inputs=ask_inputs, snap=snap, run_cleanup=cleanup)
    res = asyncio.run(ns["replay"](str(_write(tmp_path, CAP))))
    assert res.status == "STUCK" and ran == ["open"] and res.cleanup == ""

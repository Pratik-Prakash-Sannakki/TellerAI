"""Every status returns what was read. A read-only run whose checkpoint was picked after logout is SUCCESS."""
import asyncio

import pytest

SCREEN = [("Balance", (40, 300, 120, 320)), ("$515.50", (200, 300, 260, 320)), ("Pay", (40, 400, 80, 420))]


def _extract(ns, name):
    return ns["SCHEMA"]["Extract"](save_as=name, target={"anchor": {"label": "Balance", "offset": [150, 0]}})


def _click(ns, text):
    return ns["SCHEMA"]["Click"](target={"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}})


def _cap(ns, steps, outputs, checkpoint="Customer Login"):
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=steps, checkpoint=checkpoint,
                            outputs=[{"name": n, "type": "currency", "description": n} for n in outputs])


@pytest.fixture
def env(ns, mk_look):
    lk = mk_look(SCREEN)

    async def take_look():
        ns["STATE"].look = lk
        return lk

    async def snap():
        return None

    async def click(step, point, cap):
        return True

    class Stops:
        async def ask(self, *a, **k):
            return "stop"

    ns.update(take_look=take_look, snap=snap, CFG=ns["Config"](check_s=0, scroll_retries=0), CONTROL=Stops())
    ns["ACTIONS"] = {**ns["ACTIONS"], "click": click}
    ns["STATE"].look = lk
    return ns


def _finish(ns, cap):
    return asyncio.run(ns["finish"](cap, None, []))


def test_a_failed_run_still_returns_what_it_read(env) -> None:
    ns = env
    res = _finish(ns, _cap(ns, [_extract(ns, "balance"), _click(ns, "Nowhere")], ["balance", "other"],
                           checkpoint="Done"))
    assert res.status != "SUCCESS" and res.outputs == {"balance": "$515.50"}


def test_missing_outputs_are_named_in_the_reason(env) -> None:
    ns = env
    res = _finish(ns, _cap(ns, [_extract(ns, "balance")], ["balance", "available"], checkpoint="Pay"))
    assert res.status == "FAILED" and res.reason == "outputs not read: ['available']"
    assert res.outputs == {"balance": "$515.50"}


def test_partial_label_when_not_success(env) -> None:
    ns = env
    R = ns["ReplayResult"]
    assert R("FAILED", {"b": "1"}, []).outputs_line == "partial outputs (run did not succeed): {'b': '1'}"
    assert R("SUCCESS", {"b": "1"}, []).outputs_line == "outputs: {'b': '1'}"


def test_read_only_run_with_a_login_page_checkpoint_is_success(env) -> None:
    ns = env
    res = _finish(ns, _cap(ns, [_click(ns, "Pay"), _extract(ns, "balance")], ["balance"]))
    assert res.status == "SUCCESS" and res.outputs == {"balance": "$515.50"}
    assert res.reason == "checkpoint looked for after cleanup; all outputs read"


def test_a_run_with_a_send_is_not_rescued_this_way(env) -> None:
    ns = env
    click = ns["ACTIONS"]["click"]

    async def sending(step, point, cap):
        ns["STATE"].gated = True                # a send went through the human gates
        return await click(step, point, cap)

    ns["ACTIONS"]["click"] = sending
    res = _finish(ns, _cap(ns, [_click(ns, "Pay"), _extract(ns, "balance")], ["balance"]))
    assert res.status == "FAILED" and res.reason == "checkpoint text not on the final screen"
    assert res.outputs == {"balance": "$515.50"}


def test_not_rescued_when_the_last_main_step_is_not_an_extract(env) -> None:
    ns = env
    res = _finish(ns, _cap(ns, [_extract(ns, "balance"), _click(ns, "Pay")], ["balance"]))
    assert res.status == "FAILED"


def test_the_gate_marks_a_human_approved_send(ns) -> None:
    class Route:
        request = type("R", (), {"method": "POST", "url": "https://parabank.parasoft.com/x", "post_data": ""})()

        async def continue_(self, **_):
            return None

    ns["STATE"].allow_send = True                  # the login click: exempt, not a gated send
    asyncio.run(ns["guard_send"](Route()))
    assert ns["STATE"].gated is False

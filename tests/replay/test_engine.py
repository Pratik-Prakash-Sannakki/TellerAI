"""The step loop on a fake page: success, one retry, never re-send, stuck on a miss."""
import asyncio

import pytest

LOGIN = [("Username", (40, 100, 100, 120)), ("Transfer", (40, 300, 110, 320))]


class FakeControl:
    def __init__(self) -> None:
        self.asked: list[str] = []

    async def ask(self, title, details, mode, **_) -> str:
        self.asked.append(mode)
        return "stop"


@pytest.fixture
def engine(ns, mk_look):
    """ns with a fake page: `take_look` returns the fixed look; actions are scripted."""
    lk = mk_look(LOGIN)

    async def take_look():
        ns["STATE"].look = lk
        return lk

    ns["take_look"] = take_look
    ns["CONTROL"] = FakeControl()
    ns["STATE"].look = lk
    return ns


def _cap(ns, *steps):
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=list(steps), checkpoint="Transfer")


def _click(ns, text: str):
    return ns["SCHEMA"]["Click"](target={"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}})


def _type(ns, value: str):
    return ns["SCHEMA"]["Type"](value=value, target={"anchor": {"label": "Username", "offset": [150, 0]}})


def _script(ns, action: str, results: list[bool], send: bool = False) -> list:
    calls: list = []

    async def fake(step, point, cap):
        calls.append(point)
        ns["STATE"].sent = send
        return results[len(calls) - 1]

    ns["ACTIONS"] = {**ns["ACTIONS"], action: fake}
    return calls


def _walk(ns, cap):
    try:
        return asyncio.run(ns["walk"](cap, None, []))
    except ns["Stop"] as s:
        return s


def test_success_with_drift(engine) -> None:
    ns = engine
    calls = _script(ns, "click", [True])
    step = _click(ns, "Transfer")
    res = _walk(ns, _cap(ns, step))
    assert res.status == "SUCCESS" and calls == [(75, 310)]
    assert res.drift == [{"step": 0, "action": "click", "rung": "rung1", "point": (75, 310), "attempt": 1,
                         "checked": True}]


def test_failed_check_retried_once(engine) -> None:
    ns = engine
    calls = _script(ns, "type", [False, True])
    ns["STATE"].values = {"x": "v"}          # already given, so nothing is asked
    step = _type(ns, "{{x}}")
    assert _walk(ns, _cap(ns, step)).status == "SUCCESS" and len(calls) == 2


def test_send_never_retried(engine) -> None:
    ns = engine
    calls = _script(ns, "click", [False, True], send=True)
    step = _click(ns, "Transfer")
    res = _walk(ns, _cap(ns, step))
    assert res.status == "STUCK" and len(calls) == 1 and ns["CONTROL"].asked == ["rescue"]


def test_secret_never_retried(engine) -> None:
    ns = engine
    calls = _script(ns, "type", [False, True])
    step = _type(ns, "{{secret:password}}")
    assert _walk(ns, _cap(ns, step)).status == "STUCK" and len(calls) == 1


def test_locate_miss_is_stuck(engine) -> None:
    ns = engine
    ns["CFG"] = ns["Config"](scroll_retries=0)
    calls = _script(ns, "click", [True])
    step = _click(ns, "Bill Pay")
    res = _walk(ns, _cap(ns, step))
    assert res.status == "STUCK" and res.reason == "target not found" and calls == []


def test_gate2_reject_is_declined(engine) -> None:
    ns = engine

    async def declined(step, point, cap):
        ns["STATE"].verdict = "DECLINED: a human said no at Gate 2. Nothing was sent."
        return False

    ns["ACTIONS"] = {**ns["ACTIONS"], "click": declined}
    step = _click(ns, "Transfer")
    assert _walk(ns, _cap(ns, step)).status == "DECLINED"

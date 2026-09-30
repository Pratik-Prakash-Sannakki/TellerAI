"""A take-over is recorded as evidence (shots, page paths, send paths, no values) and marks the result."""
import asyncio
import contextlib

import pytest

LOOK = [("Pay", (40, 300, 110, 320)), ("Done", (40, 400, 110, 420))]


class Frame:
    def __init__(self, url) -> None:
        self.url = url


class FakePage:
    def __init__(self) -> None:
        self.main_frame, self.handlers, self.url = Frame(""), [], "https://parabank.parasoft.com/parabank/x.htm"

    def on(self, event, fn) -> None:
        self.handlers.append((event, fn))

    def remove_listener(self, event, fn) -> None:
        self.handlers.remove((event, fn))

    async def screenshot(self) -> bytes:
        return b"shot"


class Route:
    def __init__(self, method, url) -> None:
        self.request = type("R", (), {"method": method, "url": url, "post_data": "amount=10"})()

    async def continue_(self, **_) -> None:
        return None


class FakeLock:
    @contextlib.asynccontextmanager
    async def open(self):
        yield


@pytest.fixture
def env(ns, mk_look):
    lk = mk_look(LOOK, png=b"shot")

    async def take_look():
        ns["STATE"].look = lk
        return lk

    ns.update(take_look=take_look, page=FakePage(), LOCK=FakeLock())
    ns["STATE"].look = lk
    return ns


class HumanControl:
    """Takes over; while 'in control', the human opens a page and sends a form."""

    def __init__(self, ns) -> None:
        self.ns = ns

    async def ask(self, title, details, mode, **_) -> str:
        if mode == "rescue":
            return "takeover"
        page = self.ns["page"]
        for event, fn in list(page.handlers):
            fn(Frame("https://x/other"))                        # an iframe: ignored
        page.main_frame.url = "https://parabank.parasoft.com/parabank/billpay.htm;jsessionid=AB12?payee=Sean"
        for event, fn in list(page.handlers):
            fn(page.main_frame)
        self.ns["STATE"].allow_send = True
        await self.ns["guard_send"](Route("POST", "https://parabank.parasoft.com/parabank/services/pay?amount=10"))
        await self.ns["guard_send"](Route("GET", "https://parabank.parasoft.com/parabank/overview.htm"))
        self.ns["STATE"].allow_send = False
        return "done"


def _cap(ns, steps, checkpoint="Done"):
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=steps, checkpoint=checkpoint)


def _click(ns, text):
    return ns["SCHEMA"]["Click"](target={"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}})


def _fail_clicks(ns) -> None:
    async def click(step, point, cap):
        return False

    ns["ACTIONS"] = {**ns["ACTIONS"], "click": click}


def _walk(ns, cap):
    return asyncio.run(ns["walk"](cap, None, []))


def test_take_over_marks_the_result_with_step_and_actions(env) -> None:
    ns = env
    ns["CONTROL"] = HumanControl(ns)
    _fail_clicks(ns)
    res = _walk(ns, _cap(ns, [_click(ns, "Pay"), _click(ns, "Pay")]))
    assert res.status == "SUCCESS"
    assert res.human[0] == {"step": 0, "reason": "the step's check failed",
                            "actions": {"pages": ["/parabank/billpay.htm"], "sends": ["/parabank/services/pay"]}}
    assert [h["step"] for h in res.human] == [0, 1]
    assert res.summary == "SUCCESS (human intervened at steps 1, 2)"
    entry = next(d for d in res.drift if d["rung"] == "human")
    assert entry["shots"] == {"start": b"shot", "end": b"shot"}
    assert ns["page"].handlers == [] and ns["STATE"].takeover is None       # listener detached


def test_no_take_over_means_an_empty_list(env) -> None:
    ns = env

    async def click(step, point, cap):
        return True

    ns["ACTIONS"] = {**ns["ACTIONS"], "click": click}
    res = _walk(ns, _cap(ns, [_click(ns, "Pay")]))
    assert res.status == "SUCCESS" and res.human == [] and res.summary == "SUCCESS"


def test_no_values_in_the_take_over_entry(env) -> None:
    ns = env
    ns["CONTROL"] = HumanControl(ns)
    _fail_clicks(ns)
    res = _walk(ns, _cap(ns, [_click(ns, "Pay")]))
    entry = {k: v for k, v in next(d for d in res.drift if d["rung"] == "human").items() if k != "shots"}
    text = repr(entry)
    assert "Sean" not in text and "amount" not in text and "10" not in text and "jsessionid" not in text


def test_sends_are_noted_only_during_a_take_over(env) -> None:
    ns = env
    ns["STATE"].allow_send = True
    asyncio.run(ns["guard_send"](Route("POST", "https://parabank.parasoft.com/parabank/services/pay")))
    assert ns["STATE"].takeover is None


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


def _real_shots(ns, page) -> None:
    """take_look screenshots the page, as the real one does."""
    lk = ns["STATE"].look

    async def take_look():
        await page.screenshot()
        ns["STATE"].look = lk
        return lk

    ns.update(page=page, take_look=take_look)


class HeldRoute(Route):
    def __init__(self, page) -> None:
        super().__init__("POST", "https://parabank.parasoft.com/parabank/billpay.htm")
        self.page, page.held, self.done = page, True, ""

    async def continue_(self, **_) -> None:
        self.page.held, self.done = False, "sent"

    async def abort(self) -> None:
        self.page.held, self.done = False, "aborted"


class GateControl:
    def __init__(self) -> None:
        self.asked: list[str] = []

    async def ask(self, title, details, mode, image=None, **_) -> str:
        self.asked.append(mode)
        await asyncio.sleep(0)
        return "approve"


def test_navigation_send_never_screenshots_and_the_gate_shows(env) -> None:
    ns = env
    _real_shots(ns, HeldPage())
    ns["CONTROL"] = GateControl()
    ns["STATE"].given = ["10"]
    route = HeldRoute(ns["page"])
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 1))
    assert ns["CONTROL"].asked == ["confirm", "approve"] and route.done == "sent"
    assert ns["page"].shots == 0


def test_take_over_survives_a_screenshot_timeout(env) -> None:
    ns = env
    ns["CFG"] = ns["Config"](snap_s=0.05)
    _real_shots(ns, HeldPage())
    ns["CONTROL"] = HumanControlSimple()
    ns["page"].held = True                                  # a send is stuck for the whole take-over
    evidence = asyncio.run(asyncio.wait_for(ns["rescue"](0, _click(ns, "Pay"), "why"), 2))
    assert evidence["shots"] == {"start": None, "end": None}
    assert ns["STATE"].human[0]["step"] == 0


class HumanControlSimple:
    async def ask(self, title, details, mode, **_) -> str:
        return "takeover" if mode == "rescue" else "done"


class DoneWhileSending:
    """The human clicks Done just as their form POST is held: the gate must still show and finish."""

    def __init__(self, ns) -> None:
        self.ns, self.asked, self.task = ns, [], None

    async def ask(self, title, details, mode, **_) -> str:
        self.asked.append(mode)
        if mode == "rescue":
            return "takeover"
        if mode == "takeover":
            self.task = asyncio.create_task(self.ns["guard_send"](HeldRoute(self.ns["page"])))
            await asyncio.sleep(0)                          # guard_send takes the gate first
            return "done"
        await asyncio.sleep(0.02)
        return "approve"


def test_no_deadlock_between_a_pending_gate_and_done(env) -> None:
    ns = env
    _real_shots(ns, HeldPage())
    ns["STATE"].given = ["10"]
    ns["CONTROL"] = ctl = DoneWhileSending(ns)
    evidence = asyncio.run(asyncio.wait_for(ns["rescue"](0, _click(ns, "Pay"), "why"), 2))
    assert ctl.asked == ["rescue", "takeover", "confirm", "approve"] and ctl.task.done()
    assert evidence["shots"]["end"] == b"shot"            # taken after the gate released the send
    assert evidence["actions"]["sends"] == ["/parabank/billpay.htm"]


class HangPage(HeldPage):
    """`evaluate` also never returns while a request is held, as live."""

    def __init__(self, dropdowns=()) -> None:
        super().__init__()
        self.evals, self.dropdowns = 0, list(dropdowns)

    async def evaluate(self, js, *args):
        self.evals += 1
        while self.held:
            await asyncio.sleep(0.01)
        return [dict(d) for d in self.dropdowns]


class FormRoute(HeldRoute):
    def __init__(self, page, body="fromAccountId=13344&amount=10") -> None:
        super().__init__(page)
        self.request.post_data, self.sent_body = body, None

    async def continue_(self, url=None, post_data=None, **_) -> None:
        self.page.held, self.done, self.sent_body = False, "sent", post_data


class ScriptedControl:
    """Answers each gate from a script; records what each form offered."""

    def __init__(self, answers) -> None:
        self.answers, self.asked, self.forms = list(answers), [], []

    async def ask(self, title, details, mode, **_):
        self.asked.append(mode)
        return self.answers.pop(0)

    async def form(self, title, fields, values=None, options=None):
        self.forms.append(options)
        return self.answers.pop(0)


def test_human_post_during_a_take_over_passes_both_gates_with_no_evaluate(env) -> None:
    ns = env
    _real_shots(ns, HangPage([{"value": "13344", "text": "13344", "options": ["13344", "74838"]}]))
    ns["STATE"].takeover = {"pages": [], "sends": []}
    ns["CONTROL"] = ctl = ScriptedControl(["edit", ["74838", "20"], "approve", "approve"])
    route = FormRoute(ns["page"])
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 1))
    assert ctl.asked == ["confirm", "confirm", "approve"]          # no mismatch form first
    assert ctl.forms == [None]                                     # Edit = plain text fields
    assert route.done == "sent" and "74838" in route.sent_body
    assert ns["page"].evals == 0 and ns["page"].shots == 0


def test_agent_send_uses_the_stash_not_the_page(env) -> None:
    ns = env
    _real_shots(ns, HangPage())
    ns["STATE"].dropdowns = [{"value": "13344", "text": "13344", "options": ["13344", "74838"]}]
    ns["CONTROL"] = ctl = ScriptedControl([["13344", "10"], "approve", "approve"])
    route = FormRoute(ns["page"])
    asyncio.run(asyncio.wait_for(ns["guard_send"](route), 1))
    assert ctl.forms[0] == [["13344", "74838"], []] and route.done == "sent"
    assert ns["page"].evals == 0


def test_click_stashes_the_dropdowns_before_clicking(env) -> None:
    ns = env
    page = HangPage([{"value": "1", "text": "1", "options": ["1", "2"]}])
    order = []
    _real_shots(ns, page)

    async def act(*steps):
        order.append(("click", list(ns["STATE"].dropdowns)))
        return ns["STATE"].look

    async def settled(before):
        return True

    ns.update(act=act, settled_change=settled)
    asyncio.run(ns["do_click"](_click(ns, "Pay"), (75, 310), None))
    assert order == [("click", [{"value": "1", "text": "1", "options": ["1", "2"]}])]


def test_stash_read_on_a_held_page_times_out_to_empty(env) -> None:
    ns = env
    ns["CFG"] = ns["Config"](page_s=0.05)
    _real_shots(ns, HangPage([{"value": "1", "text": "1", "options": ["1", "2"]}]))
    ns["page"].held = True
    assert asyncio.run(asyncio.wait_for(ns["stash_dropdowns"](), 1)) == []


class NeverAnsweredGate:
    """The human clicks Done while their own send's Gate 1 is still open and never answered."""

    def __init__(self, ns) -> None:
        self.ns, self.task = ns, None

    async def ask(self, title, details, mode, **_):
        if mode == "rescue":
            return "takeover"
        if mode == "takeover":
            self.task = asyncio.create_task(self.ns["guard_send"](FormRoute(self.ns["page"])))
            await asyncio.sleep(0)
            return "done"
        await asyncio.Event().wait()                               # the gate is never answered


def test_done_hands_back_within_a_timeout_as_stuck(env) -> None:
    ns = env
    ns["CFG"] = ns["Config"](snap_s=0.05, gate_s=0.1)
    _real_shots(ns, HangPage())
    ns["CONTROL"] = ctl = NeverAnsweredGate(ns)

    async def run():
        try:
            return await asyncio.wait_for(ns["rescue"](0, _click(ns, "Pay"), "why"), 2)
        finally:
            ctl.task.cancel()

    with pytest.raises(ns["Stop"]) as e:
        asyncio.run(run())
    assert e.value.status == "STUCK" and "send" in e.value.reason
    assert ns["STATE"].human[0]["actions"]["sends"] == ["/parabank/billpay.htm"]


def test_checkpoint_reached_by_the_human_skips_the_remaining_steps(env) -> None:
    """Live: the human finished the whole form during a take-over; step 6 then 'target not found'."""
    ns = env
    done = ns["Look"](b"shot", b"shot", (ns["Element"](1, "Bill Payment Complete", ns["Box"](0, 0, 90, 10)),), "")

    class Finishes:
        async def ask(self, title, details, mode, **_):
            if mode == "rescue":
                return "takeover"
            ns["STATE"].look = done
            return "done"

    async def take_look():
        return ns["STATE"].look

    ns.update(take_look=take_look, CONTROL=Finishes())
    _fail_clicks(ns)
    tried = []
    fail = ns["ACTIONS"]["click"]

    async def click(step, point, cap):
        tried.append(step.target.ocr_text.text)
        return await fail(step, point, cap)

    ns["ACTIONS"]["click"] = click
    res = _walk(ns, _cap(ns, [_click(ns, "Pay"), _click(ns, "City"), _click(ns, "Send")],
                         checkpoint="Bill Payment Complete"))
    assert res.status == "SUCCESS" and tried == ["Pay", "Pay"]
    assert [d for d in res.drift if d.get("rung") == "skipped"] == [
        {"step": 1, "action": "click", "rung": "skipped"}, {"step": 2, "action": "click", "rung": "skipped"}]

"""human_help: one open-ended panel -> answer in words, take over, or stop."""
import ast
import asyncio
import contextlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest
from urllib.parse import urlparse

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


async def _no_watch(*actions) -> None:
    """The hand-back button has its own tests (test_handback.py); quiet here."""


async def _no_ext(script) -> None:
    return None


NO_WATCH = {"contextlib": contextlib,
            "watch_button": _no_watch, "ext_call": _no_ext}


@dataclass
class State:
    goal: str = "g"
    look: object = None
    stuck: str = "x"
    recent: list = field(default_factory=lambda: ["a"])
    fails: int = 3
    steps: int = 9
    login_blocked: bool = True
    login_tries: int = 2
    given: list = field(default_factory=list)
    takeover: object = None
    typed_secrets: set = field(default_factory=set)


class Control:
    def __init__(self, answer):
        self.answer, self.modes = answer, []

    async def ask(self, title, details, mode, image=None, who="agent"):
        self.modes.append(mode)
        return self.answer if mode == "help" else "done"


class Page:
    """Fires framenavigated like Playwright, for the main frame and for an iframe."""
    def __init__(self) -> None:
        self.url, self.main_frame, self.handlers, self.shots = "https://parabank.parasoft.com/x", \
            SimpleNamespace(url=""), [], 0

    def on(self, event, fn) -> None:
        assert event == "framenavigated"
        self.handlers.append(fn)

    def remove_listener(self, event, fn) -> None:
        self.handlers.remove(fn)

    def navigate(self, url: str, iframe: bool = False) -> None:
        frame = SimpleNamespace(url=url) if iframe else self.main_frame
        frame.url = url
        self.url = url if not iframe else self.url
        for fn in list(self.handlers):
            fn(frame)

    async def screenshot(self, **kw) -> bytes:
        self.shots += 1
        if getattr(self, "hangs", False):
            raise TimeoutError("Page.screenshot: Timeout 3000ms exceeded.")
        return f"shot{self.shots}".encode()


class Lock:
    @contextlib.asynccontextmanager
    async def open(self):
        yield


def _run(answer):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"human_help", "take_over", "snap"}]
    st, ctl = State(), Control(answer)
    ns = {"CONTROL": ctl, "HANDOFF": st, "LOCK": Lock(), "time": time, "log": lambda *a, **k: None,
          "page": Page(), "host_allowed": lambda u: True, "BASE_URL": "", "urlparse": urlparse,
          "CFG": SimpleNamespace(snap_ms=3000, handback_s=2), "PlaywrightError": TimeoutError, "asyncio": asyncio, **NO_WATCH,
          "mark_stuck": lambda r: f"STUCK: {r}", "SEND_GATE": asyncio.Lock()}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return asyncio.run(ns["human_help"]("t", "why")), st, ctl


@pytest.mark.parametrize(("answer", "start", "reset"), [
    ("say:use the checking account", "The human says: use the checking account", True),
    ("takeover", "A human took over", True),
    ("stop", "STOPPED", False),
    (None, "STOPPED", False),          # closed window fails closed
])
def test_outcomes(answer, start, reset) -> None:
    out, st, ctl = _run(answer)
    assert out.startswith(start)
    assert (st.fails == 0 and st.steps == 0 and st.stuck == "") is reset
    assert ("takeover" in ctl.modes) is (answer == "takeover")
    assert st.given == (["use the checking account"] if answer.startswith("say:") else []) \
        if answer else st.given == []


def _take_over(during, page=None):
    """Run human_help's take-over; `during(page)` is what the human does before clicking Done."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"human_help", "take_over", "snap"}]
    st, page, events = State(), page or Page(), []

    class Ctl(Control):
        async def ask(self, title, details, mode, image=None, who="agent"):
            if mode == "takeover":
                during(page, st)
            return await super().ask(title, details, mode, image, who)

    ns = {"CONTROL": Ctl("takeover"), "HANDOFF": st, "LOCK": Lock(), "time": time, "page": page,
          "log": lambda tool, args, result, **extra: events.append({"tool": tool, **extra}),
          "host_allowed": lambda u: True, "BASE_URL": "", "urlparse": urlparse,
          "CFG": SimpleNamespace(snap_ms=3000, handback_s=2), "PlaywrightError": TimeoutError, "asyncio": asyncio, **NO_WATCH,
          "mark_stuck": lambda r: f"STUCK: {r}", "SEND_GATE": asyncio.Lock()}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["human_help"]("t", "why"))
    return events[-1], page, st


def test_take_over_records_page_paths_and_sends_as_evidence() -> None:
    def human(page, st):
        page.navigate("https://parabank.parasoft.com/parabank/billpay.htm?payee=Sean&amount=10")
        page.navigate("https://ads.example/frame?x=1", iframe=True)      # not the main frame
        st.takeover.append({"kind": "send", "path": "/parabank/services/bank/billpay"})  # via guard_send
        page.navigate("https://parabank.parasoft.com/parabank/overview.htm")
    ev, page, st = _take_over(human)
    assert ev["tool"] == "take_over" and ev["recordable"] is False
    assert ev["actions"] == [{"kind": "page", "path": "/parabank/billpay.htm"},
                             {"kind": "send", "path": "/parabank/services/bank/billpay"},
                             {"kind": "page", "path": "/parabank/overview.htm"}]
    assert "Sean" not in str(ev["actions"]) and "amount" not in str(ev["actions"])
    assert ev["shot_before"] == b"shot1" and ev["shot_after"] == b"shot2"


def test_listener_is_removed_after_hand_back() -> None:
    _, page, st = _take_over(lambda page, st: None)
    assert page.handlers == [] and st.takeover is None


def test_a_screenshot_that_times_out_still_hands_back_cleanly() -> None:
    """Live crash: Register (a form POST) held by guard_send -> shot_after timed out after 30s."""
    page = Page()
    page.hangs = True
    ev, page, st = _take_over(lambda page, st: None, page)
    assert ev["shot_before"] is None and ev["shot_after"] is None
    assert page.handlers == [] and st.takeover is None


def test_no_deadlock_when_a_gate_is_pending_at_done() -> None:
    """The human pressed Register (gate held, its question on top), then clicked Done in the tab.
    Hand-back waits for that gate instead of screenshotting; answering it finishes both."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"human_help", "take_over", "snap"}]
    st, page, gate, events = State(), Page(), asyncio.Lock(), []
    answers: dict = {}

    class Ctl:
        async def ask(self, title, details, mode, image=None, who="agent"):
            if mode == "help":
                return "takeover"
            fut = asyncio.get_running_loop().create_future()
            answers[mode] = fut
            return await fut

    async def gate_held():                       # guard_send holding a navigation, gate on screen
        async with gate:
            await Ctl().ask("Gate 1 of 2", "", "confirm")

    ns = {"CONTROL": Ctl(), "HANDOFF": st, "LOCK": Lock(), "time": time, "page": page,
          "log": lambda tool, args, result, **extra: events.append({"tool": tool, **extra}),
          "host_allowed": lambda u: True, "BASE_URL": "", "urlparse": urlparse,
          "CFG": SimpleNamespace(snap_ms=3000, handback_s=2), "PlaywrightError": TimeoutError, "asyncio": asyncio, **NO_WATCH,
          "mark_stuck": lambda r: f"STUCK: {r}", "SEND_GATE": gate}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)

    async def scenario():
        helped = asyncio.create_task(ns["human_help"]("t", "why"))
        await asyncio.sleep(0)
        held = asyncio.create_task(gate_held())
        await asyncio.sleep(0)
        answers["takeover"].set_result("done")          # Done while the gate is pending
        await asyncio.sleep(0.01)
        assert not helped.done()                        # waits for the gate, does not screenshot
        answers["confirm"].set_result("approve")        # the human answers the gate
        return await asyncio.wait_for(asyncio.gather(helped, held), 2)

    out, _ = asyncio.run(scenario())
    assert out.startswith("A human took over") and events[-1]["tool"] == "take_over"


def test_done_with_a_send_held_forever_ends_the_take_over_as_stuck() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"human_help", "take_over", "snap"}]
    st, page, gate, events = State(), Page(), asyncio.Lock(), []

    class Ctl:
        async def ask(self, title, details, mode, image=None, who="agent"):
            return "takeover" if mode == "help" else "done"

    ns = {"CONTROL": Ctl(), "HANDOFF": st, "LOCK": Lock(), "time": time, "page": page,
          "log": lambda tool, args, result, **extra: events.append(tool),
          "host_allowed": lambda u: True, "BASE_URL": "", "urlparse": urlparse, "asyncio": asyncio, **NO_WATCH,
          "CFG": SimpleNamespace(snap_ms=3000, handback_s=0.05), "PlaywrightError": TimeoutError,
          "SEND_GATE": gate, "mark_stuck": lambda r: f"STUCK: {r}"}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)

    async def scenario():
        await gate.acquire()                     # a guard_send that never finishes
        return await asyncio.wait_for(ns["human_help"]("t", "why"), 2)

    out = asyncio.run(scenario())
    assert out.startswith("STUCK: a send the human started was still held")
    assert page.handlers == [] and st.takeover is None and events == ["take_over"]

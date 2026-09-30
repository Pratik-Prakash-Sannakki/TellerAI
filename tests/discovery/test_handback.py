"""take_over's hand-back: the extension's toolbar button (never the site), with no idle reminder (the user asked for none)."""
import ast
import asyncio
import base64
import contextlib
import html
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
IDLE = 0.05


class Win:
    def __init__(self) -> None:
        self.html, self.fronted = "", 0

    async def set_content(self, content: str) -> None:
        self.html = content

    def is_closed(self) -> bool:
        return False

    async def bring_to_front(self) -> None:
        self.fronted += 1


class Site(Win):
    """The site tab: a still screen unless `screen` changes; fires framenavigated. Records every
    call made on it, so a test can prove the hand-back window never touches the site."""
    def __init__(self) -> None:
        super().__init__()
        self.url, self.main_frame, self.handlers = "https://parabank.parasoft.com/x", \
            SimpleNamespace(url=""), []
        self.screen, self.calls = b"still", []

    def on(self, event, fn) -> None:
        self.calls.append("on")
        self.handlers.append(fn)

    def remove_listener(self, event, fn) -> None:
        self.calls.append("remove_listener")
        self.handlers.remove(fn)

    def navigate(self, url: str) -> None:
        self.main_frame.url = self.url = url
        for fn in list(self.handlers):
            fn(self.main_frame)

    async def screenshot(self, **kw) -> bytes:
        self.calls.append("screenshot")
        return self.screen

    async def bring_to_front(self) -> None:
        self.calls.append("bring_to_front")
        await super().bring_to_front()


class Ext:
    """The hand-back extension's service worker: a click counter and a badge. Never the site."""
    def __init__(self, hang: bool = False, fail: bool = False) -> None:
        self.clicks, self.calls, self.hang, self.fail = 0, [], hang, fail

    async def evaluate(self, script: str):
        self.calls.append(script)
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise TimeoutError("Target closed")               # PlaywrightError here
        return self.clicks if "handbackClicked" in script else None


class Lock:
    @contextlib.asynccontextmanager
    async def open(self):
        yield


def _load():
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body
            if getattr(n, "name", None) in {"take_over", "snap", "ControlWindow",
                                            "_img", "ext_call", "watch_button"}
            or (isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "_CONTROLS")]
    site, win = Site(), Win()
    handoff = SimpleNamespace(takeover=None, dropdowns=[], typed_secrets=set())
    ns = {"asyncio": asyncio, "base64": base64, "contextlib": contextlib, "html": html, "time": time,
          "urlparse": urlparse,
          "page": site, "HANDOFF": handoff, "LOCK": Lock(), "log": lambda *a, **k: None,
          "host_allowed": lambda u: True, "BASE_URL": "", "PlaywrightError": TimeoutError,
          "SEND_GATE": asyncio.Lock(), "screens_same": lambda a, b: a == b, "EXT": Ext(),
          "CFG": SimpleNamespace(snap_ms=3000, handback_s=1, ext_s=0.05, ext_poll_s=0.01)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    ns["CONTROL"] = ns["ControlWindow"](win)
    return ns, site, win


def _modes(ns) -> list[str]:
    return [q[2] for _, q in ns["CONTROL"]._stack]


async def _until(cond, limit: float = 1.0) -> None:
    end = time.monotonic() + limit
    while not cond():
        assert time.monotonic() < end, "timed out"
        await asyncio.sleep(0.005)


def test_done_in_the_takeover_itself_cancels_the_watcher() -> None:
    async def run():
        ns, site, win = _load()
        before = asyncio.all_tasks()
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        ns["CONTROL"].on_reply("done")
        await asyncio.wait_for(task, 1)
        await asyncio.sleep(IDLE * 3)
        assert asyncio.all_tasks() == before and _modes(ns) == []
    asyncio.run(run())


def _modes_set(ext) -> list[str]:
    return [c for c in ext.calls if c.startswith("setMode")]


def test_the_badge_reads_you_during_the_take_over_then_ai() -> None:
    async def run():
        ns, site, win = _load()
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        assert _modes_set(ns["EXT"]) == ["setMode('YOU')"]
        ns["CONTROL"].on_reply("done")
        await asyncio.wait_for(task, 1)
        assert _modes_set(ns["EXT"]) == ["setMode('YOU')", "setMode('AI')"]
    asyncio.run(run())


def test_a_click_on_the_toolbar_button_hands_back() -> None:
    async def run():
        ns, site, win = _load()
        ns["EXT"].clicks = 4                                     # clicks from an earlier take-over
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        await asyncio.sleep(0.05)
        assert not task.done()                                   # the old count is the baseline
        ns["EXT"].clicks += 1
        assert await asyncio.wait_for(task, 1) is None
    asyncio.run(run())


def test_the_button_poll_is_cancelled_even_when_the_take_over_fails() -> None:
    async def run():
        ns, site, win = _load()
        before = asyncio.all_tasks()

        class Boom(Exception):
            pass

        async def broken(*a, **k):
            raise Boom
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        ns["SEND_GATE"].acquire = broken                         # hand-back itself blows up
        ns["CONTROL"].on_reply("done")
        with contextlib.suppress(Boom):
            await asyncio.wait_for(task, 1)
        await asyncio.sleep(0.05)
        assert asyncio.all_tasks() == before                     # no poll left running
        assert _modes_set(ns["EXT"])[-1] == "setMode('AI')"
    asyncio.run(run())


def test_the_button_never_touches_the_site_page() -> None:
    async def run():
        ns, site, win = _load()
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        ns["EXT"].clicks += 1
        await asyncio.wait_for(task, 1)
        # only what take_over already did before the button existed: listen, screenshot, front
        assert set(site.calls) <= {"on", "remove_listener", "screenshot", "bring_to_front"}
    asyncio.run(run())


def test_no_extension_still_hands_back_from_the_control_tab() -> None:
    async def run():
        for ext in (None, Ext(fail=True), Ext(hang=True)):
            ns, site, win = _load()
            ns["EXT"] = ext
            task = asyncio.create_task(ns["take_over"]("why"))
            await _until(lambda: _modes(ns) == ["takeover"])
            ns["CONTROL"].on_reply("done")                       # the control tab's Done still works
            assert await asyncio.wait_for(task, 1) is None
    asyncio.run(run())


def test_take_over_message_points_at_the_toolbar_button() -> None:
    src = SRC.read_text()
    assert "click the Agent hand-back icon in the browser toolbar" in src


def test_no_idle_reminder_ever_interrupts_the_take_over() -> None:
    """The user's rule: no "are you done?" prompts in between. Only the take-over panel is shown."""
    async def run():
        ns, site, win = _load()
        task = asyncio.create_task(ns["take_over"]("why"))
        await _until(lambda: _modes(ns) == ["takeover"])
        await asyncio.sleep(0.3)
        assert _modes(ns) == ["takeover"]
        ns["CONTROL"].on_reply("done")
        await asyncio.wait_for(task, 1)
    asyncio.run(run())

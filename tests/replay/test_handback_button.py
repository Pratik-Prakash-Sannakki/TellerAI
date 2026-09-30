"""Take-over: the hand-back extension's toolbar button (its service worker, never the site page)."""
import asyncio
import contextlib

import pytest
from playwright.async_api import Error as PlaywrightError


class SitePage:
    """The site page: any call made on it for the button is a bug."""

    def __init__(self) -> None:
        self.calls, self.main_frame, self.url = [], object(), "https://parabank.parasoft.com/parabank/x.htm"
        self.listeners = []

    async def screenshot(self) -> bytes:
        return b"shot"

    async def evaluate(self, *a):
        self.calls.append("evaluate")

    def on(self, event, fn) -> None:
        self.listeners.append((event, fn))

    def remove_listener(self, event, fn) -> None:
        self.listeners.remove((event, fn))


class Ext:
    """The extension's service worker: a click counter and a badge."""

    def __init__(self, clicks=0, hang=False, fail=False) -> None:
        self.clicks, self.calls, self.hang, self.fail = clicks, [], hang, fail

    async def evaluate(self, script: str):
        self.calls.append(script)
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise PlaywrightError("Target closed")
        return self.clicks if "handbackClicked" in script else None

    @property
    def modes(self) -> list[str]:
        return [c for c in self.calls if c.startswith("setMode")]


class Lock:
    @contextlib.asynccontextmanager
    async def open(self):
        yield


class Human:
    """Takes over, then (optionally) clicks the toolbar button; never clicks the panel's Done."""

    def __init__(self, click=None) -> None:
        self.click, self.asked = click, []

    async def ask(self, title, details, mode, **_):
        self.asked.append((mode, details))
        if mode == "rescue":
            return "takeover"
        if self.click:
            await asyncio.sleep(0.05)
            self.click()
        await asyncio.Event().wait()


class PanelDone(Human):
    async def ask(self, title, details, mode, **_):
        self.asked.append((mode, details))
        await asyncio.sleep(0.05)
        return "takeover" if mode == "rescue" else "done"


@pytest.fixture
def env(ns, mk_look):
    lk = mk_look([("Pay", (0, 0, 40, 10))], png=b"x")

    async def take_look():
        ns["STATE"].look = lk
        return lk

    ns.update(take_look=take_look, LOCK=Lock(), page=SitePage(),
              CFG=ns["Config"](page_s=0.05, snap_s=0.05, ext_s=0.05, ext_poll_s=0.01))
    ns["STATE"].look = lk
    return ns


def _rescue(ns):
    step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": "Pay"}, "anchor": {"label": "Pay", "offset": [0, 0]}})
    return asyncio.run(asyncio.wait_for(ns["rescue"](0, step, "why"), 2))


def _click(ns):
    def press():
        ns["EXT"].clicks += 1
    return press


def test_the_badge_reads_you_then_ai(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = Ext(), Human(_click(env))
    _rescue(ns)
    assert ns["EXT"].modes == ["setMode('YOU')", "setMode('AI')"]


def test_a_click_count_rise_hands_back(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = Ext(clicks=3), Human(_click(env))     # 3 = an earlier take-over's
    _rescue(ns)
    assert ns["STATE"].human[0]["step"] == 0 and ns["EXT"].clicks == 4


def test_an_old_click_count_alone_does_not_hand_back(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = Ext(clicks=3), Human()
    with pytest.raises(asyncio.TimeoutError):
        _rescue(ns)


def test_the_poll_is_cancelled_in_finally(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = Ext(), Human(_click(env))

    async def run():
        before = asyncio.all_tasks()
        step = ns["SCHEMA"]["Click"](target={"ocr_text": {"text": "Pay"}, "anchor": {"label": "Pay", "offset": [0, 0]}})
        await ns["rescue"](0, step, "why")
        polls = len(ns["EXT"].calls)
        await asyncio.sleep(0.05)
        assert asyncio.all_tasks() == before and len(ns["EXT"].calls) == polls

    asyncio.run(asyncio.wait_for(run(), 2))


@pytest.mark.parametrize("ext", [None, Ext(fail=True), Ext(hang=True)])
def test_a_missing_or_broken_extension_does_not_break_the_take_over(env, ext) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = ext, PanelDone()          # the control tab's Done still works
    _rescue(ns)
    assert ns["STATE"].human[0]["step"] == 0


def test_no_site_page_call_is_made_for_it(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = Ext(), Human(_click(env))
    _rescue(ns)
    assert ns["page"].calls == []


def test_take_over_message_points_at_the_toolbar_button(env) -> None:
    ns = env
    ns["EXT"], ns["CONTROL"] = None, (ctl := PanelDone())
    _rescue(ns)
    assert "click the Agent hand-back icon in the browser toolbar" in dict(ctl.asked)["takeover"]
    assert "puzzle-piece" in dict(ctl.asked)["takeover"]

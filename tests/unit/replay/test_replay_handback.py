"""The toolbar hand-back button during a rescue (its service worker, never the site page).
Ported from tests/replay/test_handback_button.py."""

from __future__ import annotations

import asyncio

import pytest
from playwright.async_api import Error as PlaywrightError

from cua.config import BrowserConfig, ReplayConfig
from cua.replay import rescue
from cua.replay.context import Ctx
from cua.schema import ReplayResult
from tests.unit.replay.helpers import click, make_replay_ctx, mk_look, screen
from tests.unit.replay.test_replay_rescue import FakePage

# --- the toolbar hand-back button (test_handback_button.py) --------------------------------


class SitePage(FakePage):
    """The site page: any call made on it for the button is a bug."""

    async def evaluate(self, *a: object) -> None:
        self.calls.append("evaluate")


class Ext:
    """The extension's service worker: a click counter and a badge."""

    def __init__(self, clicks: int = 0, hang: bool = False, fail: bool = False) -> None:
        self.clicks, self.calls, self.hang, self.fail = clicks, [], hang, fail

    async def evaluate(self, script: str) -> object:
        self.calls.append(script)
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise PlaywrightError("Target closed")
        return self.clicks if "handbackClicked" in script else None

    @property
    def modes(self) -> list[str]:
        return [c for c in self.calls if c.startswith("setMode")]


class Human:
    """Takes over, then (optionally) clicks the toolbar button; never clicks the panel's Done."""

    def __init__(self, ext: Ext | None = None, click_it: bool = False) -> None:
        self.ext, self.click_it, self.asked = ext, click_it, []

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        self.asked.append((mode, details))
        if mode == "rescue":
            return "takeover"
        if self.click_it and self.ext:
            await asyncio.sleep(0.05)
            self.ext.clicks += 1
        await asyncio.Event().wait()
        return ""


class PanelDone(Human):
    async def ask(self, title: str, details: str, mode: str, **_: object) -> str:
        self.asked.append((mode, details))
        await asyncio.sleep(0.05)
        return "takeover" if mode == "rescue" else "done"


def _bctx(ext: object, control: object) -> Ctx:
    ctx = make_replay_ctx(
        SitePage(),
        control,
        ext=ext,
        cfg=ReplayConfig(page_s=0.05, snap_s=0.05),
        bcfg=BrowserConfig(ext_s=0.05, ext_poll_s=0.01),
    )
    screen(ctx, mk_look([("Pay", (0, 0, 40, 10))], png=b"x"))
    return ctx


async def _rescue(ctx: Ctx) -> dict[str, object]:
    return await asyncio.wait_for(rescue.rescue(ctx, 0, click("Pay"), "why"), 2)  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_the_badge_reads_you_then_ai() -> None:
    ext = Ext()
    await _rescue(_bctx(ext, Human(ext, True)))
    assert ext.modes == ["setMode('YOU')", "setMode('AI')"]


@pytest.mark.asyncio
async def test_a_click_count_rise_hands_back() -> None:
    ext = Ext(clicks=3)  # 3 = an earlier take-over's
    ctx = _bctx(ext, Human(ext, True))
    await _rescue(ctx)
    assert ctx.run.human[0]["step"] == 0 and ext.clicks == 4


@pytest.mark.asyncio
async def test_an_old_click_count_alone_does_not_hand_back() -> None:
    ext = Ext(clicks=3)
    with pytest.raises(TimeoutError):
        await _rescue(_bctx(ext, Human(ext)))


@pytest.mark.asyncio
async def test_the_poll_is_cancelled_in_finally() -> None:
    ext = Ext()
    ctx = _bctx(ext, Human(ext, True))
    before = asyncio.all_tasks()
    await rescue.rescue(ctx, 0, click("Pay"), "why")
    polls = len(ext.calls)
    await asyncio.sleep(0.05)
    assert asyncio.all_tasks() == before and len(ext.calls) == polls


@pytest.mark.asyncio
@pytest.mark.parametrize("ext", [None, Ext(fail=True), Ext(hang=True)])
async def test_a_missing_or_broken_extension_does_not_break_the_take_over(ext: Ext | None) -> None:
    ctx = _bctx(ext, PanelDone())  # the control tab's Done still works
    await _rescue(ctx)
    assert ctx.run.human[0]["step"] == 0


@pytest.mark.asyncio
async def test_no_site_page_call_is_made_for_it() -> None:
    ext = Ext()
    ctx = _bctx(ext, Human(ext, True))
    await _rescue(ctx)
    assert ctx.page.calls == []  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_take_over_message_points_at_the_toolbar_button() -> None:
    ctl = PanelDone()
    await _rescue(_bctx(None, ctl))
    assert "click the Agent hand-back icon in the browser toolbar" in dict(ctl.asked)["takeover"]
    assert "puzzle-piece" in dict(ctl.asked)["takeover"]


def test_result_type_is_the_schema_one() -> None:
    assert ReplayResult("SUCCESS", {}, []).summary == "SUCCESS"

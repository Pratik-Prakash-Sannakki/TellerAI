"""Step actions on fakes: whole-field read (A), tolerant word match (B), late page change (D),
navigate/http errors, selects. Ported from tests/replay/
test_checks.py, test_http_errors.py, test_select_index.py and test_adjacent_selects.py
(extracts: test_replay_extract.py)."""

from __future__ import annotations

import asyncio

import cv2
import numpy as np
import pytest

from cua.config import BrowserConfig, ReplayConfig
from cua.replay import engine, steps
from cua.replay.context import Ctx
from cua.replay.locate import find_text, same_label
from cua.replay.wiring import note_response
from cua.schema import Capability, Stop
from cua.vision import Look, encode, screens_same
from tests.unit.replay.helpers import (
    click,
    make_replay_ctx,
    mk_look,
    navigate,
    screen,
    select,
    type_,
)

BASE = "https://parabank.parasoft.com/parabank"
FIELD = (300, 100, 500, 130)  # a drawn input box; its centre is (400, 115)


def _form_png() -> bytes:
    img = np.full((300, 700, 3), 255, np.uint8)
    cv2.rectangle(img, FIELD[:2], FIELD[2:], (160, 160, 160), 1)
    return encode(img)


def _white(lines: tuple[int, ...] = ()) -> bytes:
    img = np.full((400, 600, 3), 255, np.uint8)
    for y in lines:  # a few short text-like strokes: a small change
        img[y : y + 6, 20:120] = 0
    return encode(img)


# --- checks (test_checks.py) ---------------------------------------------------------------


def test_field_box_is_the_drawn_input() -> None:
    lk = mk_look([], _form_png())
    ctx = make_replay_ctx(look=lk)
    b = steps.field_box(ctx, lk, (400, 115))
    assert (
        abs(b.x1 - 300) <= 2
        and abs(b.x2 - 500) <= 2
        and abs(b.y1 - 100) <= 2
        and abs(b.y2 - 130) <= 2
    )


def test_short_value_at_left_edge_is_read() -> None:
    lk = mk_look([("State", (220, 108, 270, 124)), ("IL", (306, 108, 322, 124))], _form_png())
    ctx = make_replay_ctx(look=lk)
    assert steps.read_field(ctx, lk, (400, 115)) == "IL"


class Page:
    url = "https://parabank.parasoft.com/parabank/billpay.htm"

    def __init__(self) -> None:
        self.mouse: object = None

    async def wait_for_timeout(self, ms: float) -> None:
        await asyncio.sleep(ms / 1000)  # like Playwright: the loop runs meanwhile

    async def evaluate(self, js: str, *args: object) -> list[object]:
        return []


@pytest.mark.asyncio
async def test_click_waits_for_a_late_page_change(monkeypatch: pytest.MonkeyPatch) -> None:
    blank = mk_look([("Pay", (10, 10, 40, 30))], encode(np.full((80, 80, 3), 255, np.uint8)))
    done = mk_look([("Complete", (10, 10, 70, 30))], encode(np.zeros((80, 80, 3), np.uint8)))
    looks = iter([blank, done, done])
    ctx = make_replay_ctx(Page(), look=blank)

    async def act(c: Ctx, *s: object) -> Look:
        c.run.look = blank
        return blank

    async def shoot() -> Look:
        return next(looks, done)

    ctx.shoot = shoot
    monkeypatch.setattr(steps, "act", act)
    assert await steps.do_click(ctx, click("Pay"), (25, 20), None) is True  # type: ignore[arg-type]
    assert ctx.run.look is done


def _click_env(gate_starts_after_s: float) -> tuple[Ctx, object, Look]:
    """The real `act`. The click's send takes the gate only after the settle, as a slow route can."""
    form = mk_look([("TRANSFER", (10, 10, 70, 30))], _white())
    done = mk_look([("Transfer Complete!", (10, 10, 170, 30))], _white((60,)))
    page = Page()
    now = {"look": form}
    ctx = make_replay_ctx(
        page,
        cfg=ReplayConfig(check_s=0.05, poll_ms=10),
        bcfg=BrowserConfig(settle_ms=10),
        look=form,
    )

    async def gates_then_answer() -> None:
        await asyncio.sleep(gate_starts_after_s)
        async with ctx.guard.lock:  # the human takes longer than check_s
            ctx.run.sent = True
            await asyncio.sleep(0.2)
            ctx.run.verdict = "SENT: a human approved both gates."
        now["look"] = done  # the site answers once the send is released

    class Mouse:
        async def click(self, *a: float) -> None:
            asyncio.get_running_loop().create_task(gates_then_answer())

    async def shoot() -> Look:
        return now["look"]

    page.mouse = Mouse()
    ctx.shoot = shoot
    step = click("TRANSFER")
    return ctx, step, done


@pytest.mark.asyncio
@pytest.mark.parametrize("gate_starts_after_s", [0, 0.03])
async def test_a_send_approved_after_check_s_still_passes_with_no_rescue(
    gate_starts_after_s: float,
) -> None:
    """Live bug: the Transfer click sent (both gates approved) but its check said 'failed'."""
    ctx, step, done = _click_env(gate_starts_after_s)
    assert await asyncio.wait_for(steps.do_click(ctx, step, (40, 20), None), 2) is True  # type: ignore[arg-type]
    assert ctx.run.look is done


def test_a_small_change_with_new_text_counts_as_a_change() -> None:
    a = mk_look([("TRANSFER", (10, 10, 70, 30))], _white())
    b = mk_look([("Transfer Complete!", (10, 10, 170, 30))], _white((60,)))
    ctx = make_replay_ctx()
    assert screens_same(a.png, b.png, ctx.bcfg)  # too small for the pixel check alone
    assert steps.changed(ctx, a, b) and not steps.changed(ctx, a, a)


@pytest.mark.asyncio
async def test_a_one_character_value_is_checked_by_pixels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live: Address '1' failed twice: OCR does not read a lone character. The pixels changed."""
    before, after = mk_look([], _white()), mk_look([("l", (20, 55, 30, 70))], _white((60,)))
    ctx = make_replay_ctx()

    async def act(c: Ctx, *s: object) -> Look:
        c.run.look = after
        return after

    monkeypatch.setattr(steps, "act", act)
    step = type_("{{address}}", "Address:", (0, 0))
    ctx.run.look, ctx.run.values = before, {"address": "1"}
    assert await steps.do_type(ctx, step, (70, 62), None) is True  # type: ignore[arg-type]
    ctx.run.look, ctx.run.values = before, {"address": "12 Main"}
    assert await steps.do_type(ctx, step, (70, 62), None) is False  # type: ignore[arg-type]


async def _same_screen_click(navigated: bool) -> bool:
    lk = mk_look([("Accounts Overview", (10, 10, 170, 30))], _white())
    page = Page()
    ctx = make_replay_ctx(
        page, cfg=ReplayConfig(check_s=0.05, poll_ms=10), bcfg=BrowserConfig(settle_ms=0)
    )
    screen(ctx, lk)

    class Mouse:
        async def click(self, *a: float) -> None:
            if navigated:  # a main-frame response for the same path
                ctx.run.http = (200, "/parabank/overview.htm")
                ctx.run.navs += 1

    page.mouse = Mouse()
    return await steps.do_click(ctx, click("Accounts Overview"), (90, 20), None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_a_same_url_reload_counts_as_a_change() -> None:
    assert await _same_screen_click(navigated=True) is True


@pytest.mark.asyncio
async def test_a_click_on_plain_text_with_no_navigation_still_fails() -> None:
    assert await _same_screen_click(navigated=False) is False


# --- navigate + HTTP errors (test_http_errors.py) ------------------------------------------


@pytest.mark.parametrize(
    ("path", "want"),
    [
        ("/parabank/contact.htm", f"{BASE}/contact.htm"),
        ("about.htm", f"{BASE}/about.htm"),
        ("/", "https://parabank.parasoft.com/"),
    ],
)
def test_site_url_joins_like_a_browser(path: str, want: str) -> None:
    assert steps.site_url(BASE, path) == want


class GotoPage:
    def __init__(self) -> None:
        self.went: list[str] = []
        self.main_frame = PAGE_FRAME

    async def goto(self, url: str) -> None:
        self.went.append(url)


PAGE_FRAME = object()


@pytest.mark.asyncio
async def test_navigate_goes_to_the_joined_url_once() -> None:
    page = GotoPage()
    ctx = make_replay_ctx(page)
    ctx.run.values = {"page": "contact.htm"}
    cp = Capability(
        name="t",
        description="t",
        base_url=BASE,
        viewport=(1280, 800),
        steps=[navigate("/parabank/{{page}}")],
        checkpoint="x",
    )
    await steps.do_navigate(ctx, cp.steps[0], None, cp)  # type: ignore[arg-type]
    assert page.went == [f"{BASE}/contact.htm"]


class Resp:
    def __init__(self, url: str, status: int, main: bool = True, nav: bool = True) -> None:
        self.url, self.status = url, status
        self.frame = PAGE_FRAME if main else object()
        self.request = type(
            "Q", (), {"is_navigation_request": lambda s: nav, "frame": self.frame}
        )()


def test_only_the_main_documents_status_is_kept() -> None:
    ctx = make_replay_ctx(GotoPage())
    note_response(ctx, Resp(f"{BASE}/img.png", 404, nav=False))  # a sub-resource: ignored
    note_response(ctx, Resp("https://x/frame", 500, main=False))  # an iframe: ignored
    assert ctx.run.http is None
    note_response(ctx, Resp(f"{BASE}/parabank/contact.htm;jsessionid=AB?x=1", 404))
    assert ctx.run.http == (404, "/parabank/parabank/contact.htm")


async def _judge(http: tuple[int, str] | None, text: str) -> bool:
    ctx = make_replay_ctx(look=mk_look([(text, (0, 0, 200, 20))]))
    ctx.run.http = http
    ctx.run.outcomes = [
        {"text": o.text, "status": o.status, "meaning": o.meaning} for o in ctx.site.outcomes
    ]
    cp = Capability(
        name="t",
        description="t",
        base_url=BASE,
        viewport=(1280, 800),
        steps=[navigate("/x")],
        checkpoint="x",
    )
    return await engine.judge(ctx, 0, "", cp, None, [])


@pytest.mark.asyncio
async def test_a_404_navigation_is_failed_not_a_business_outcome() -> None:
    with pytest.raises(Stop) as e:
        await _judge((404, "/parabank/parabank/contact.htm"), "Not Found")
    assert e.value.status == "FAILED" and e.value.reason == "page returned HTTP 404"
    assert e.value.observed == "/parabank/parabank/contact.htm"


@pytest.mark.asyncio
async def test_a_200_page_with_not_found_text_is_still_a_business_outcome() -> None:
    with pytest.raises(Stop) as e:
        await _judge((200, "/parabank/find.htm"), "Account not found")
    assert e.value.status == "BUSINESS_OUTCOME"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body", ['{"title":"Not Found","status":404}', 'x {"type":"err","status":500} y']
)
async def test_a_raw_json_error_body_is_failed(body: str) -> None:
    with pytest.raises(Stop) as e:
        await _judge(None, body)
    assert e.value.status == "FAILED" and e.value.reason == "page is a raw error response"


@pytest.mark.asyncio
async def test_a_normal_page_passes() -> None:
    assert await _judge((200, "/parabank/overview.htm"), "Accounts Overview") is False


# --- selects (test_select_index.py, test_adjacent_selects.py) ------------------------------


class SelectPage:
    def __init__(self) -> None:
        self.args: list[list[object]] = []

    async def evaluate(self, js: str, args: list[object]) -> list[object]:
        self.args.append(args)
        return ["13344", "15120"] if args[2] is None else [872, 355, args[2]]

    async def wait_for_timeout(self, ms: float) -> None:
        return None


async def _select(
    index: int | None, seen: str, mp: pytest.MonkeyPatch
) -> tuple[bool, list[list[object]]]:
    page = SelectPage()
    ctx = make_replay_ctx(page)
    screen(ctx, mk_look([(seen, (720, 345, 900, 365))]))
    mp.setattr(steps, "read_field", lambda c, look, point: seen)
    ctx.run.values = {"to_account": "15120"}
    step = select("to_account", index=index)
    return await steps.do_select(ctx, step, (780, 355), None), page.args  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_the_step_index_reaches_the_page_and_merged_ocr_confirms_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ok, args = await _select(1, "to account #|15120", monkeypatch)
    assert ok is True and [a[3] for a in args] == [1, 1]


@pytest.mark.asyncio
async def test_an_old_step_without_an_index_selects_by_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ok, args = await _select(None, "15120", monkeypatch)
    assert ok is True and [a[3] for a in args] == [None, None]


@pytest.mark.asyncio
async def test_the_confirm_is_not_fooled_by_a_longer_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (await _select(1, "to account #|151200", monkeypatch))[0] is False


def test_from_label_is_not_the_to_anchor() -> None:
    cfg = ReplayConfig()
    assert not same_label("From account #", "to account #", cfg)
    assert not same_label("to account #", "From account #", cfg)


def test_the_right_label_still_matches() -> None:
    cfg = ReplayConfig()
    assert same_label("to account #", "to account #", cfg)
    assert same_label("to account #|15120", "to account #", cfg)
    assert same_label("From account #[", "From account #", cfg)
    assert same_label("Log ln", "Log In", cfg)


def test_the_to_anchor_finds_the_to_label_not_the_from_label() -> None:
    look = mk_look(
        [("From account #", (488, 346, 578, 364)), ("to account #", (720, 346, 800, 364))]
    )
    el = find_text(look, "to account #", 1, ReplayConfig(), same_label)
    assert el is not None and el.text == "to account #"


def test_value_glued_to_hash_confirms_the_option() -> None:
    ctx = make_replay_ctx()
    assert steps.shows_option(ctx, "to account #15120", "15120")
    assert steps.shows_option(ctx, "to account #|15120", "15120")
    assert not steps.shows_option(ctx, "to account #151200", "15120")
    assert not steps.shows_option(ctx, "to account #15121", "15120")

"""click / type_text / type_secret / select_option / scroll / open_path / observe: what each does to
the run and logs. The page is an ActTab; ``context.act``/``look`` are stubbed at each tool module.

Ported from tests/discovery/test_send_settle.py (landed), test_wandering.py (open_path) and
test_no_values_stored.py (no typed value reaches the log); the rest pins the moved bodies.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

import pytest

from cua.discovery.context import Ctx
from cua.discovery.tools import act, human, nav, observe
from cua.discovery.tools.act import landed
from cua.vision.look import Look
from tests.fakes import ActTab, blank_png, make_ctx, make_look, make_session

PNG, DARK = blank_png(), blank_png(shade=0)
FORM = [("Payee Name:", (10, 60, 110, 80)), ("Amount:", (10, 100, 80, 120))]
TOOLS_SRC = Path(act.__file__).parent


class Driven:
    """The stubbed page work: every ``act`` call and the looks it returns."""

    def __init__(self, ctx: Ctx, after: Look) -> None:
        self.ctx, self.after, self.acts = ctx, after, 0
        self.on_act: Callable[[], None] = lambda: None

    async def act(self, ctx: Ctx, *steps: Callable[[], object]) -> Look:
        for step in steps:
            await step()  # type: ignore[misc]
        self.acts += 1
        self.on_act()
        ctx.run.look = self.after
        return self.after

    async def look(self, ctx: Ctx) -> Look:
        ctx.run.look = self.after
        return self.after


def _driven(
    monkeypatch: pytest.MonkeyPatch, before: Look, after: Look | None = None, **kw: object
) -> Driven:
    ctx = make_ctx(make_session(ActTab(before.url)), **kw)  # type: ignore[arg-type]
    ctx.run.look = before
    d = Driven(ctx, after or before)
    for mod in (act, nav, observe):
        monkeypatch.setattr(mod, "look", d.look)
    for mod in (act, nav):
        monkeypatch.setattr(mod, "act", d.act)
    monkeypatch.setattr(act, "crop", lambda *a: b"crop")
    return d


def _tool(ctx: Ctx, name: str):  # type: ignore[no-untyped-def]
    tools = [
        *act.make_act_tools(ctx),
        *nav.make_nav_tools(ctx),
        *observe.make_observe_tools(ctx),
        *human.make_human_tools(ctx),
    ]
    return {t.name: t for t in tools}[name]


def _helped(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """human_help stubbed: the reasons it was called with (it would wait on the control window)."""
    reasons: list[str] = []

    async def help_(ctx: Ctx, title: str, reason: str) -> str:
        reasons.append(reason)
        return "HELP"

    monkeypatch.setattr(human, "human_help", help_)
    return reasons


def _head(out: object) -> str:
    return out if isinstance(out, str) else out[0]["text"]  # type: ignore[index,no-any-return]


# --- landed / blocks ---


def test_landed_keeps_only_new_fixed_text() -> None:
    ctx = make_ctx()
    ctx.run.given, ctx.run.typed_texts = ["Jane Doe"], {"42"}
    before = make_look([("Bill Payment Service", (0, 0, 9, 9)), ("Request Loan", (0, 20, 9, 29))])
    after = make_look(
        [
            ("Bill Payment Complete", (0, 0, 9, 9)),
            ("Bill Payment to Jane Doe in the amount of $42.00", (0, 10, 9, 19)),
            ("13344", (0, 20, 9, 29)),
            ("Request Loan", (0, 30, 9, 39)),
        ]
    )
    assert landed(ctx, before, after) == ["Bill Payment Complete"]


def test_blocks_lists_the_look_and_hides_secret_values() -> None:
    ctx = make_ctx()
    lk = make_look([("u-val", (1, 2, 3, 4))], png=PNG)
    text, image = observe.blocks(ctx, "Hi.", lk)
    assert text["text"] == f"Hi.\nURL: {lk.url}\nText on screen:\n[1] '<username>' box=(1,2,3,4)"
    assert image["type"] == "image"
    assert image["mime_type"] == "image/png"


@pytest.mark.asyncio
async def test_observe_takes_a_new_look(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG))
    out = await _tool(d.ctx, "observe").ainvoke({})
    assert _head(out).startswith("Current page.")


# --- open_path ---


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [404, 200])
async def test_open_path_records_the_http_status_and_the_absolute_path(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG))
    d.ctx.page.status = status  # type: ignore[attr-defined]
    out = _head(await _tool(d.ctx, "open_path").ainvoke({"path": "contact.htm"}))
    ev = d.ctx.run.log[-1]
    assert ev["status"] == status
    assert ev["path"] == "/app/contact.htm"
    assert ev["from_texts"] == ["Payee Name:", "Amount:"]
    assert d.ctx.page.url == "https://example.test/app/contact.htm"
    if status == 404:  # noqa: PLR2004
        assert ev["result"].startswith("HTTP ERROR 404")
        assert "does not exist" in out
    else:
        assert out.startswith("Opened contact.htm.")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "goal", "why"),
    [
        ("https://evil.test/x", "", "host is not allowed"),
        ("register.htm", "", "'register.htm' is not allowed"),
        ("find.htm?id=99", "find 12", "query values must come from the goal"),
    ],
)
async def test_open_path_refuses_other_hosts_deny_words_and_ungiven_query_values(
    monkeypatch: pytest.MonkeyPatch, path: str, goal: str, why: str
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), goal=goal)
    out = _head(await _tool(d.ctx, "open_path").ainvoke({"path": path}))
    assert out.startswith("REFUSED")
    assert why in out
    assert "goto" not in d.ctx.page.calls  # type: ignore[attr-defined]


# --- scroll ---


@pytest.mark.asyncio
async def test_scroll_moves_the_wheel_by_the_configured_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), make_look(FORM, png=DARK))
    out = _head(await _tool(d.ctx, "scroll").ainvoke({"direction": "up"}))
    assert out.startswith("Scrolled up.")
    assert d.ctx.page.inputs == [("move", (640.0, 400.0)), ("wheel", (0, -600))]  # type: ignore[attr-defined]
    assert d.ctx.run.log[-1]["args"] == {"direction": "up", "x": None, "y": None}


@pytest.mark.asyncio
async def test_scroll_with_no_change_is_the_end_of_the_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG))
    assert _head(await _tool(d.ctx, "scroll").ainvoke({"direction": "down"})).startswith("BOTTOM")


# --- click ---

BUTTONS = [*FORM, ("Log In", (300, 200, 360, 220)), ("Register", (300, 240, 380, 260))]


@pytest.mark.asyncio
async def test_a_click_that_changes_the_screen_is_logged_with_where_it_led(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    after = make_look([*BUTTONS, ("Welcome", (10, 10, 90, 30))], png=DARK)
    d = _driven(monkeypatch, make_look(BUTTONS, png=PNG), after, secrets={})
    out = _head(await _tool(d.ctx, "click").ainvoke({"ref": 3}))
    assert out.startswith("Clicked 'Log In'.")
    ev = d.ctx.run.log[-1]
    assert ev["text"] == "Log In"
    assert ev["login"] is True
    assert ev["new_texts"] is True
    assert ev["loaded"] is False
    assert ev["navigated"] is False
    assert "landed" not in ev
    assert d.ctx.run.login_tries == 1
    assert d.ctx.run.allow_send is False  # only around the login click
    assert d.ctx.page.inputs == [("click", (330.0, 210.0))]  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_a_click_with_no_change_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(BUTTONS, png=PNG))
    out = _head(await _tool(d.ctx, "click").ainvoke({"x": 500, "y": 500}))
    assert out.startswith("NO CHANGE after clicking (500, 500)")


@pytest.mark.asyncio
async def test_a_denied_word_is_refused_without_clicking(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(BUTTONS, png=PNG))
    out = _head(await _tool(d.ctx, "click").ainvoke({"ref": 4}))
    assert out.startswith("REFUSED: 'Register'")
    assert d.acts == 0
    assert d.ctx.run.log[-1]["text"] == "Register"


@pytest.mark.asyncio
async def test_a_click_on_a_box_already_filled_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look([("16785", (10, 10, 60, 30))], png=PNG))
    d.ctx.run.typed_texts = {"16785"}
    out = _head(await _tool(d.ctx, "click").ainvoke({"ref": 1}))
    assert out.startswith("REFUSED: that number is text inside a box you already filled")
    assert d.acts == 0


@pytest.mark.asyncio
async def test_a_click_that_leaves_the_site_goes_back(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(BUTTONS, png=PNG))
    d.on_act = lambda: setattr(d.ctx.page, "url", "https://evil.test/")
    helped = _helped(monkeypatch)
    assert await _tool(d.ctx, "click").ainvoke({"ref": 1}) == "HELP"  # BLOCKED: the human is asked
    assert helped == ["left the allowed site. Went back."]
    assert d.ctx.run.log[-1]["result"] == "BLOCKED: left the allowed site. Went back."
    assert "go_back" in d.ctx.page.calls  # type: ignore[attr-defined]
    assert d.ctx.run.log[-1]["loaded"] is True


@pytest.mark.asyncio
async def test_a_sent_click_records_what_the_page_showed(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(BUTTONS, png=PNG))  # the screen does not change
    d.on_act = lambda: setattr(d.ctx.run, "verdict", "SENT (approved).")
    await _tool(d.ctx, "click").ainvoke({"ref": 2})
    ev = d.ctx.run.log[-1]
    assert ev["result"] == "Clicked 'Amount:'."  # a send that went out is a real step
    assert ev["landed"] == []


# --- type_text / select_option: values never reach the log ---


@pytest.mark.asyncio
async def test_type_text_types_a_goal_value_and_logs_where_never_what(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    after = make_look([*FORM, ("Sean", (150, 60, 200, 80))], png=PNG)
    d = _driven(monkeypatch, make_look(FORM, png=PNG), after, goal="pay Sean")
    out = _head(await _tool(d.ctx, "type_text").ainvoke({"text": "Sean", "x": 175, "y": 70}))
    assert out.startswith("Typed at (175, 70). Box shows 'Payee Name: Sean'.")
    assert d.ctx.run.typed_texts == {"Sean"}
    assert d.ctx.run.entered == {"Payee Name:": "Sean"}
    ev = d.ctx.run.log[-1]
    assert ev["label"] == "Payee Name:"
    assert ev["result"] == "Typed at (175, 70)."
    assert "Sean" not in str(ev)
    assert ("type", ("Sean",)) in d.ctx.page.inputs  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_a_value_not_in_the_goal_is_handed_to_a_human(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), goal="pay someone")
    asked: list[object] = []

    async def fills(ctx: Ctx, fields: list[object], **kw: object) -> str:
        asked.append((fields, kw))
        return "A human gave: Payee Name:."

    monkeypatch.setattr(act, "human_fills", fills)
    out = _head(await _tool(d.ctx, "type_text").ainvoke({"text": "Sean", "x": 175, "y": 70}))
    assert out.startswith("A human gave")
    assert asked == [([((175, 70), "Payee Name:")], {})]
    assert d.acts == 0


@pytest.mark.asyncio
async def test_select_option_chooses_and_logs_the_index(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), goal="from Checking")

    async def choose(ctx: Ctx, point: tuple[int, int], option: str) -> int | None:
        return 2 if option == "Checking" else None

    monkeypatch.setattr(act, "choose_option", choose)
    out = _head(
        await _tool(d.ctx, "select_option").ainvoke({"option": "Checking", "x": 175, "y": 110})
    )
    assert out.startswith("Selected 'Checking' at (175, 110).")
    ev = d.ctx.run.log[-1]
    assert ev["index"] == 2  # noqa: PLR2004
    assert ev["label"] == "Amount:"
    assert "Checking" not in str(ev)
    assert d.ctx.run.entered == {"Amount:": "Checking"}


@pytest.mark.asyncio
async def test_select_option_not_in_the_list_is_stuck(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), goal="from Gold")
    helped = _helped(monkeypatch)

    async def no_choice(ctx: Ctx, point: tuple[int, int], option: str) -> int | None:
        return None

    monkeypatch.setattr(act, "choose_option", no_choice)
    out = await _tool(d.ctx, "select_option").ainvoke({"option": "Gold", "x": 175, "y": 110})
    assert out == "HELP"
    assert helped == ["'Gold' is not an option in 'Amount:'"]


def _logged_arg_keys(tool: str) -> list[set[str]]:
    """The arg-dict keys of every ``log(ctx, "<tool>", {...}, ...)`` call in the tool modules."""
    keys = []
    for path in TOOLS_SRC.glob("*.py"):
        for n in ast.walk(ast.parse(path.read_text())):
            if (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", "")) == "log"
                and len(n.args) > 2  # noqa: PLR2004
                and isinstance(n.args[1], ast.Constant)
                and n.args[1].value == tool
            ):
                d = n.args[2]
                keys.append({k.value for k in d.keys} if isinstance(d, ast.Dict) else set())  # type: ignore[union-attr]
    return keys


def test_typed_and_selected_values_never_reach_the_log() -> None:
    """Banking rule (ported from test_no_values_stored.py, now on the package's own source)."""
    for tool, banned in [
        ("type_text", {"text"}),
        ("select_option", {"option"}),
        ("type_secret", {"value"}),
        ("request_value", {"value"}),
    ]:
        calls = _logged_arg_keys(tool)
        assert calls, tool
        for keys in calls:
            assert not (keys & banned), f"{tool} logs a value"


def test_no_saved_form() -> None:
    assert not any("last_form" in p.read_text() for p in TOOLS_SRC.glob("*.py"))


# --- type_secret ---


@pytest.mark.asyncio
async def test_an_unknown_secret_names_the_known_ones(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG))
    out = _head(await _tool(d.ctx, "type_secret").ainvoke({"name": "pin", "ref": 1}))
    assert out.startswith("UNKNOWN SECRET 'pin'. Use one of: ['password', 'username']")


@pytest.mark.asyncio
async def test_type_secret_types_by_name_and_never_logs_the_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG), make_look(FORM, png=DARK))
    out = _head(await _tool(d.ctx, "type_secret").ainvoke({"name": "username", "x": 175, "y": 70}))
    assert out.startswith("Typed secret 'username' at (175, 70).\nURL:")
    assert d.ctx.run.typed_secrets == {"username"}
    assert d.ctx.run.log[-1]["args"] == {"secret_name": "username"}
    assert "u-val" not in str(d.ctx.run.log)


@pytest.mark.asyncio
async def test_a_password_shown_as_plain_text_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    after = make_look([*FORM, ("p-val", (150, 60, 200, 80))], png=DARK)
    d = _driven(monkeypatch, make_look(FORM, png=PNG), after)
    helped = _helped(monkeypatch)
    out = await _tool(d.ctx, "type_secret").ainvoke({"name": "password", "x": 175, "y": 70})
    assert out == "HELP"
    assert d.ctx.run.look is None
    assert d.ctx.run.log[-1]["result"] == "STOP: secret visible"
    assert helped == ["the box shows the secret as plain text. Call ask_human; do not observe."]


@pytest.mark.asyncio
async def test_nothing_typed_when_the_point_is_no_box(monkeypatch: pytest.MonkeyPatch) -> None:
    d = _driven(monkeypatch, make_look(FORM, png=PNG))
    out = _head(await _tool(d.ctx, "type_secret").ainvoke({"name": "username", "x": 175, "y": 70}))
    assert out.startswith("NOTHING TYPED at (175, 70)")
    assert not d.ctx.run.typed_secrets


@pytest.mark.asyncio
async def test_type_text_logs_the_value_shape_never_the_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    after = make_look([*FORM, ("123.45", (150, 100, 200, 120))], png=PNG)
    d = _driven(monkeypatch, make_look(FORM, png=PNG), after, goal="pay 123.45")
    await _tool(d.ctx, "type_text").ainvoke({"text": "123.45", "x": 175, "y": 110})
    ev = d.ctx.run.log[-1]
    assert ev["shapes"] == ["currency", "number"]
    assert "123.45" not in str(ev)

"""Tool guards: the event log, the step budget, repeats, login tries, click gates, targets."""

from __future__ import annotations

import dataclasses

import pytest

from cua.config import STEP_ACTIONS, DiscoveryConfig
from cua.discovery.tools import build_tools, guard, human
from cua.discovery.tools.guard import (
    after_login_click,
    gate_click,
    log,
    mark_stuck,
    needs_human_value,
    note_call,
    one_at_a_time,
    resolve_point,
)
from cua.vision.look import Box, Element, Look
from tests.fakes import SITE, make_ctx, make_session

LOOK = Look(b"", b"", (Element(4, "Pay", Box(10, 10, 50, 30)),), "u")


def test_log_appends_one_event_with_the_first_result_line_and_page_url() -> None:
    ctx = make_ctx()
    log(ctx, "click", {"ref": 1}, "Clicked.\nmore", (1, 2), b"c", own=None)
    assert ctx.run.log == [
        {
            "tool": "click",
            "args": {"ref": 1},
            "result": "Clicked.",
            "point": (1, 2),
            "url": "https://example.test/x",
            "crop": b"c",
            "own": None,
        }
    ]


def test_log_attaches_the_models_why_when_there_is_one() -> None:
    ctx = make_ctx()
    ctx.run.why = "The form is open, so I fill it."
    log(ctx, "click", {"ref": 1}, "Clicked.")
    assert ctx.run.log[-1]["why"] == "The form is open, so I fill it."


def test_mark_stuck_sets_the_reason() -> None:
    ctx = make_ctx()
    assert mark_stuck(ctx, "why") == "STUCK: why"
    assert ctx.run.stuck == "why"


def test_the_same_call_three_times_is_stuck() -> None:
    ctx = make_ctx()
    assert note_call(ctx, "click", {"ref": 1}) is None
    assert note_call(ctx, "click", {"ref": 1}) is None
    assert note_call(ctx, "click", {"ref": 1}) == "STUCK: repeated click 3 times"
    assert note_call(make_ctx(), "click", {"ref": 2}) is None


def test_a_login_failure_text_blocks_login_for_the_run() -> None:
    ctx = make_ctx()
    out = after_login_click(ctx, "Error! The username could NOT BE VERIFIED.")
    assert out is not None
    assert out.startswith("STOP: login failed")
    assert ctx.run.login_blocked


def test_empty_fields_on_login_is_a_retry_not_a_failure() -> None:
    """Live: the site answered 'Please enter a username and password' (the boxes were empty: the
    typing missed). That is not a wrong password; one more try typing the secrets is right."""
    site = dataclasses.replace(SITE, login_empty_texts=("please enter a username and password",))
    ctx = make_ctx(dataclasses.replace(make_session(), site=site))
    ctx.run.typed_secrets = {"username", "password"}
    out = after_login_click(ctx, "Error! Please enter a username and password.")
    assert out is not None
    assert out.startswith("RETRY:")
    assert not ctx.run.login_blocked
    assert ctx.run.typed_secrets == set()  # the secrets must be typed again


def test_login_is_blocked_after_the_limit() -> None:
    ctx = make_ctx(cfg=DiscoveryConfig(login_limit=2))
    assert after_login_click(ctx, "") is None
    assert not ctx.run.login_blocked
    assert after_login_click(ctx, "") is None
    assert ctx.run.login_blocked


@pytest.mark.asyncio
async def test_gate_click_refuses_deny_words_declined_and_blocked_login() -> None:
    ctx = make_ctx()
    assert (await gate_click(ctx, "Register")).startswith("REFUSED")  # type: ignore[union-attr]
    assert await gate_click(ctx, "Registered users") is None  # whole words only
    ctx.run.declined.add("send")
    assert (await gate_click(ctx, "Send")).startswith("DECLINED")  # type: ignore[union-attr]
    ctx.run.login_blocked = True
    assert (await gate_click(ctx, "Log In")).startswith("BLOCKED")  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_login_needs_every_secret_typed_first() -> None:
    ctx = make_ctx()
    out = await gate_click(ctx, "Log In")
    assert (
        out == "NOT YET: type ['password', 'username'] with type_secret first, one box each, "
        "then click this."
    )
    ctx.run.typed_secrets = {"username", "password"}
    assert await gate_click(ctx, "Log In") is None
    assert await gate_click(ctx, "Accounts") is None


def test_needs_human_value_for_sensitive_empty_or_ungiven_values() -> None:
    ctx = make_ctx(goal="pay 10 to Jane")
    assert not needs_human_value(ctx, "Jane", "Payee")
    assert needs_human_value(ctx, "Jane", "SSN")
    assert needs_human_value(ctx, "", "Payee")
    assert needs_human_value(ctx, "Bob", "Payee")


def test_resolve_point() -> None:
    ctx = make_ctx()
    assert resolve_point(ctx, 4, None, None) == "LOOK FIRST: call observe."
    ctx.run.look = LOOK
    assert resolve_point(ctx, 4, None, None) == (30, 20)
    assert resolve_point(ctx, 9, None, None).startswith("STALE")  # type: ignore[union-attr]
    assert resolve_point(ctx, 4, 1, 2).startswith("BAD TARGET")  # type: ignore[union-attr]
    assert resolve_point(ctx, None, 1, None).startswith("BAD TARGET")  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_resolve_point_bounds_are_the_current_canvas(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = make_ctx()
    ctx.run.look = LOOK
    monkeypatch.setattr(guard, "canvas", lambda c: (100, 50))
    assert resolve_point(ctx, None, 99, 49) == (99, 49)
    assert resolve_point(ctx, None, 100, 1) == "OUT OF VIEW: (100,1) is outside 100x50."


def _tool(ctx, results: list[object]):  # type: ignore[no-untyped-def]
    @one_at_a_time(ctx)
    async def click(ref: int = 0) -> object:
        """Doc."""
        out = results.pop(0)
        if isinstance(out, BaseException):
            raise out
        if callable(out):
            return out()
        return out

    return click


@pytest.fixture
def helped(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []

    async def fake_help(ctx: object, title: str, reason: str) -> str:
        calls.append((title, reason))
        return f"HELP {reason}"

    monkeypatch.setattr(human, "human_help", fake_help)
    return calls


@pytest.mark.asyncio
async def test_one_at_a_time_keeps_the_name_and_docstring() -> None:
    fn = _tool(make_ctx(), [])
    assert fn.__name__ == "click"
    assert fn.__doc__ == "Doc."


@pytest.mark.asyncio
async def test_one_at_a_time_counts_steps_and_resets_the_verdict(helped: list[object]) -> None:
    ctx = make_ctx()
    ctx.run.verdict = "old"
    assert await _tool(ctx, ["Clicked."])(ref=1) == "Clicked."
    assert ctx.run.steps == 1
    assert ctx.run.verdict == ""
    assert ctx.run.fails == 0


@pytest.mark.asyncio
async def test_over_the_step_budget_offers_control(helped: list[tuple[str, str]]) -> None:
    ctx = make_ctx(cfg=DiscoveryConfig(step_budget=1))
    tool = _tool(ctx, ["a", "b"])
    await tool(ref=1)
    assert await tool(ref=2) == "HELP 1 steps without finishing"
    assert helped == [("The agent is stuck", "1 steps without finishing")]


@pytest.mark.asyncio
async def test_a_stuck_verdict_offers_control_a_declined_one_is_returned(
    helped: list[object],
) -> None:
    ctx = make_ctx()

    def stuck() -> str:
        ctx.run.verdict = "STUCK: No value confirmed for x. Nothing was sent."
        return "Clicked."

    def declined() -> str:
        ctx.run.verdict = "DECLINED by a human."
        return "Clicked."

    tool = _tool(ctx, [stuck, declined])
    assert await tool(ref=1) == "HELP No value confirmed for x. Nothing was sent."
    assert await tool(ref=2) == "DECLINED by a human."


@pytest.mark.asyncio
async def test_failed_results_in_a_row_ask_the_human(helped: list[tuple[str, str]]) -> None:
    ctx = make_ctx()
    tool = _tool(ctx, ["NO CHANGE a", "STALE b", "OUT OF VIEW c\nmore"])
    await tool(ref=1)
    await tool(ref=2)
    assert await tool(ref=3) == "HELP 3 tries failed. Last: OUT OF VIEW c"
    assert helped[-1][0] == "The agent is unsure"


@pytest.mark.asyncio
async def test_a_sent_verdict_prefixes_a_block_result(helped: list[object]) -> None:
    ctx = make_ctx()

    def sent() -> list[dict[str, str]]:
        ctx.run.verdict = "SENT: a human approved both gates."
        return [{"type": "text", "text": "Clicked."}]

    out = await _tool(ctx, [sent])(ref=1)
    assert out == [{"type": "text", "text": "SENT: a human approved both gates. Clicked."}]


@pytest.mark.asyncio
async def test_calls_run_one_at_a_time_on_the_runs_lock() -> None:
    ctx = make_ctx()
    seen: list[bool] = []

    def check() -> str:
        seen.append(ctx.run.act_lock.locked())
        return "ok"

    await _tool(ctx, [check])(ref=1)
    assert seen == [True]
    assert not ctx.run.act_lock.locked()


def test_log_takes_point_and_crop_by_keyword_too() -> None:
    ctx = make_ctx()
    log(ctx, "stuck", {"reason": "r"}, "stopped")
    log(ctx, "click", {}, "ok", point=(3, 4), crop=b"c", own=None)
    assert ctx.run.log[0]["point"] is None
    assert ctx.run.log[0]["crop"] is None
    assert ctx.run.log[1] == {
        "tool": "click",
        "args": {},
        "result": "ok",
        "point": (3, 4),
        "url": "https://example.test/x",
        "crop": b"c",
        "own": None,
    }


def _only(*actions: str):  # type: ignore[no-untyped-def]
    site = dataclasses.replace(SITE, allowed_actions=frozenset(actions))
    return make_ctx(dataclasses.replace(make_session(), site=site))


@pytest.mark.asyncio
async def test_a_tool_whose_action_is_not_allowed_is_refused_and_logged(
    helped: list[object],
) -> None:
    ctx = _only("extract")
    ran: list[str] = []

    @one_at_a_time(ctx)
    async def scroll(direction: str = "down") -> str:
        """Doc."""
        ran.append(direction)
        return "Scrolled."

    out = await scroll(direction="down")
    assert out == (
        "REFUSED: action 'scroll' is not in allowed_actions. "
        "Use another tool or reply 'STUCK: <why>'."
    )
    assert ran == []
    assert ctx.run.log[-1]["tool"] == "scroll"
    assert ctx.run.log[-1]["args"] == {"direction": "down"}
    assert ctx.run.log[-1]["result"].startswith("REFUSED: action 'scroll'")


@pytest.mark.asyncio
async def test_allowed_and_non_site_tools_still_run(helped: list[object]) -> None:
    ctx = _only("click")

    @one_at_a_time(ctx)
    async def observe() -> str:
        """Doc."""
        return "Looked."

    assert await _tool(ctx, ["Clicked."])(ref=1) == "Clicked."
    assert await observe() == "Looked."
    assert ctx.run.log == []


def test_every_built_tool_has_an_action_type() -> None:
    names = {t.name for t in build_tools(make_ctx())}
    assert names == set(guard.TOOL_ACTIONS)
    assert {a for a in guard.TOOL_ACTIONS.values() if a} <= STEP_ACTIONS


def test_log_never_stores_the_session_token_or_the_query() -> None:
    ctx = make_ctx()
    ctx.page.url = "https://example.test/app/activity.htm;jsessionid=AB12CD?id=98765"  # type: ignore[misc]
    log(ctx, "click", {}, "ok")
    assert ctx.run.log[0]["url"] == "https://example.test/app/activity.htm"

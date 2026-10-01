"""Tool guards: the event log, one call at a time, the step budget, repeats, login tries, click
gates, and target resolution.

Moved from discovery.py 486-498 (log, needs_human_value, mark_stuck), 606-635 (note_call,
after_login_click, gate_click), 1091-1131 (ACT_LOCK -> ``ctx.run.act_lock``, one_at_a_time,
resolve_point). Globals become ``ctx``; site words come from ``ctx.site``, limits from ``ctx.cfg``.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Awaitable, Callable
from typing import ParamSpec, cast

from cua.discovery.context import Ctx, canvas
from cua.discovery.tools import human  # module import: human.py imports this one back
from cua.discovery.tools.failed import FAILED
from cua.safety.redact import is_sensitive, norm
from cua.schema.events import Event

P = ParamSpec("P")
Result = str | list[dict[str, str]]  # a tool's text, or content blocks (text first)

# Assignment 3.4: each tool -> the capability step action it performs, checked against
# ``ctx.site.allowed_actions``. None = not a site action (looking, finishing, asking a human).
TOOL_ACTIONS: dict[str, str | None] = {
    "observe": None,
    "click": "click",
    "type_text": "type",
    "type_secret": "type",
    "select_option": "select",
    "scroll": "scroll",
    "open_path": "navigate",
    "extract_value": "extract",
    "extract_table": "extract_table",
    "finish_business_outcome": None,
    "request_missing_values": None,
    "ask_human": None,
}


def log(
    ctx: Ctx, tool: str, args: dict[str, object], result: str, *at: object, **extra: object
) -> None:
    """One event (the notebook's ``log(tool, args, result, point=None, crop=None, **extra)``):
    ``*at`` is the optional positional ``point, crop``; both may also be given by keyword."""
    point = at[0] if at else extra.pop("point", None)
    crop = at[1] if len(at) > 1 else extra.pop("crop", None)
    event: dict[str, object] = {
        "tool": tool,
        "args": args,
        "result": result.split("\n")[0],
        "point": point,
        "url": ctx.page.url,
        "crop": crop,
        **extra,
    }
    if ctx.run.why and tool in TOOL_ACTIONS:  # 3.5: why the agent made this call (masked)
        event["why"] = ctx.run.why
    ctx.run.log.append(cast("Event", event))


def needs_human_value(ctx: Ctx, value: str, label: str) -> bool:
    """D34: a sensitive field, or a value the user never gave, is typed by a human."""
    return (
        not norm(value)
        or is_sensitive(label, ctx.session.cfg.sensitive_words)
        or norm(value) not in norm(ctx.run.goal)
    )


def mark_stuck(ctx: Ctx, reason: str) -> str:
    ctx.run.stuck = reason
    return f"STUCK: {reason}"


def note_call(ctx: Ctx, tool: str, args: dict[str, object]) -> str | None:
    """The same call N times in a row means STUCK."""
    limit = ctx.cfg.repeat_limit
    key = f"{tool}:{json.dumps(args, sort_keys=True, default=str)}"
    ctx.run.recent = [*ctx.run.recent, key][-limit:]
    if len(ctx.run.recent) == limit and len(set(ctx.run.recent)) == 1:
        return mark_stuck(ctx, f"repeated {tool} {limit} times")
    return None


def refuse_action(ctx: Ctx, tool: str, args: dict[str, object]) -> str | None:
    """3.4: a tool whose action type the site does not allow is refused (and logged), not run."""
    action = TOOL_ACTIONS.get(tool)
    if action is None or action in ctx.site.allowed_actions:
        return None
    msg = (
        f"REFUSED: action '{action}' is not in allowed_actions. "
        "Use another tool or reply 'STUCK: <why>'."
    )
    log(ctx, tool, args, msg)
    return msg


def after_login_click(ctx: Ctx, screen_text: str) -> str | None:
    """D69: at most N login tries; a failure text on screen stops login for the run."""
    ctx.run.login_tries += 1
    texts = ctx.site.login_failure_texts
    failed = next((t for t in texts if t in screen_text.casefold()), None)
    if failed or ctx.run.login_tries >= ctx.cfg.login_limit:
        ctx.run.login_blocked = True
    if failed:
        return f"STOP: login failed ('{failed}'). Do not try again. Reply 'STUCK: <why>'."
    return None


async def gate_click(ctx: Ctx, text: str | None, image: bytes | None = None) -> str | None:
    """D33: None means go ahead; otherwise the refusal the tool returns. No per-click approval."""
    name, site = norm(text), ctx.site
    if name and any(re.search(rf"\b{re.escape(w)}\b", name) for w in site.deny_words):
        return f"REFUSED: '{text}' is not allowed. Find another way or reply 'STUCK: <why>'."
    if name in ctx.run.declined:
        return "DECLINED earlier by a human. Do not retry. Reply 'DECLINED: <why>' and stop."
    if name in site.login_words and ctx.run.login_blocked:
        return "BLOCKED: login hit its limit. Do not try again. Reply 'STUCK: <why>'."
    if name in site.login_words and (missing := sorted(set(ctx.secrets) - ctx.run.typed_secrets)):
        return f"NOT YET: type {missing} with type_secret first, one box each, then click this."
    return None  # moving around needs no approval; anything that sends data meets the two gates


def resolve_point(ctx: Ctx, ref: int | None, x: int | None, y: int | None) -> tuple[int, int] | str:
    look = ctx.run.look
    if look is None:
        return "LOOK FIRST: call observe."
    if (ref is None) == (x is None or y is None):
        return "BAD TARGET: give either ref, or both x and y."
    if ref is not None:
        el = look.get(ref)
        return el.box.center if el else f"STALE: [{ref}] is not in the latest look. Call observe."
    w, h = canvas(ctx)
    assert x is not None
    assert y is not None
    return (x, y) if 0 <= x < w and 0 <= y < h else f"OUT OF VIEW: ({x},{y}) is outside {w}x{h}."


async def _checked(ctx: Ctx, result: Result) -> Result:
    """What one_at_a_time does with a tool's result (the notebook's wrapper body after the call)."""
    run = ctx.run
    if run.verdict.startswith(("STUCK", "DECLINED")):
        return (
            await human.offer_control(ctx, run.verdict)
            if run.verdict.startswith("STUCK")
            else run.verdict
        )
    head = result if isinstance(result, str) else result[0]["text"]
    if head.startswith(("STUCK:", "STOP:", "BLOCKED:")):
        return await human.offer_control(ctx, head)
    run.fails = run.fails + 1 if head.startswith(FAILED) else 0
    if run.verdict.startswith("SENT") and not isinstance(result, str):
        result[0]["text"] = f"{run.verdict} {head}"
    if run.fails >= ctx.cfg.unsure_limit:
        return await human.human_help(
            ctx,
            "The agent is unsure",
            f"{run.fails} tries failed. Last: {head.splitlines()[0][:120]}",
        )
    return result


def one_at_a_time(
    ctx: Ctx,
) -> Callable[[Callable[P, Awaitable[Result]]], Callable[P, Awaitable[Result]]]:
    """One tool call at a time (``ctx.run.act_lock``), counted against the step budget and the
    repeat limit; a STUCK/STOP/BLOCKED result, or too many failures in a row, calls the human."""

    def decorate(fn: Callable[P, Awaitable[Result]]) -> Callable[P, Awaitable[Result]]:
        @functools.wraps(fn)
        async def wrapper(*a: P.args, **k: P.kwargs) -> Result:
            run, budget = ctx.run, ctx.cfg.step_budget
            async with run.act_lock:
                run.steps += 1
                over = run.steps > budget and mark_stuck(ctx, f"{budget} steps without finishing")
                run.verdict = ""
                name, args = fn.__name__, dict(k)
                refused = over or refuse_action(ctx, name, args) or note_call(ctx, name, args)
                result = refused or await fn(*a, **k)
                return await _checked(ctx, result)

        return wrapper

    return decorate

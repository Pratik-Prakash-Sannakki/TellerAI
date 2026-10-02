"""Calling in the human: open-ended help, a take-over of the site, and the human's own values.

Moved from discovery.py 501-518 (human_help), 530-573 (take_over, built from cua.handoff's
``ext_call``/``watch_button``/``wait_held_send`` and the session's ``SiteLock.open()``), 600-603
(offer_control), 1038-1071 (human_fills), and the human-facing tools 1653-1704
(finish_business_outcome, start_page_refusal, request_missing_values, ask_human). Globals become
``ctx``; the start page is ``ctx.site.start_url``.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Callable
from urllib.parse import urlparse

from langchain_core.tools import BaseTool, tool

from cua.discovery.context import Ctx, act, choose_option, crop, into_box, list_options, snap
from cua.discovery.recorder.types import shapes_of
from cua.discovery.run import run_values
from cua.discovery.tools import guard, observe
from cua.discovery.tools.read_helpers import where
from cua.handoff import ext_call, wait_held_send, watch_button
from cua.safety import host_allowed, is_sensitive, norm
from cua.vision.crops import element_at
from cua.vision.look import Look

Field = tuple[tuple[int, int], str]  # (point, hint)


async def human_help(ctx: Ctx, title: str, reason: str) -> str:
    """Q21, open-ended: the human answers in words, takes over the site, or stops the run."""
    run = ctx.run
    image = run.look.drawn if run.look else None
    choice = await ctx.control.ask(title, reason, "help", image=image) or "stop"
    if choice.startswith("say:") and choice[4:].strip():
        guard.log(ctx, "ask_human", {"reason": reason}, "answered")
        run.given.append(choice[4:].strip())
        result = f"The human says: {choice[4:].strip()}"
    elif choice == "takeover":
        if stuck := await take_over(ctx, reason):
            return guard.mark_stuck(ctx, stuck) + ". Reply 'STUCK: ' with it and stop."
        result = "A human took over the site and handed back. Call observe and continue the task."
    else:
        guard.log(ctx, "stuck", {"reason": reason}, "human stopped the run")
        return f"STOPPED by the human: {reason}. Reply 'STUCK: {reason}' and stop."
    run = ctx.run
    run.stuck, run.recent, run.fails, run.steps = "", [], 0, 0
    run.login_blocked, run.login_tries = False, 0
    return result


async def offer_control(ctx: Ctx, msg: str) -> str:
    """Only the reason: the first line of the tool result, without its prefix or instructions."""
    reason = msg.splitlines()[0].split(":", 1)[-1].strip().split(". Reply")[0]
    return await human_help(ctx, "The agent is stuck", reason[:200])


def _takeover_note(reason: str) -> str:
    return (
        f"{reason} Work in the site tab. When you're "
        "done, click the Agent hand-back icon in the browser toolbar (pin it "
        "once from the puzzle-piece menu), or Done in the Agent control tab. "
        "If you log in with a new user, the agent carries on from there."
    )


async def _in_control(ctx: Ctx, reason: str, on_page: Callable[[object], None]) -> str | None:
    """The take-over itself: badge YOU, unlock the site, wait for Done (panel or toolbar), then
    for a send still held at the gates. Always cleans up. Returns a STUCK reason or None."""
    s, stuck = ctx.session, None
    ctx.page.on("framenavigated", on_page)
    await ext_call(s.ext, "setMode('YOU')", s.cfg.ext_s)
    watchers = [asyncio.create_task(watch_button(s.ext, s.cfg, ctx.control))]
    try:
        async with s.lock.open():  # the human's own sends still go through both gates
            await ctx.control.ask(
                "You are in control", _takeover_note(reason), "takeover", who="human"
            )
        if not await wait_held_send(ctx.guard.lock, ctx.cfg.handback_s):
            stuck = f"a send the human started was still held {ctx.cfg.handback_s}s after Done"
    finally:
        for task in watchers:  # the button watcher is never worth failing a hand-back
            task.cancel()
        await asyncio.gather(*watchers, return_exceptions=True)
        await ext_call(s.ext, "setMode('AI')", s.cfg.ext_s)
        ctx.page.remove_listener("framenavigated", on_page)
        ctx.run.takeover = None
    return stuck


async def take_over(ctx: Ctx, reason: str) -> str | None:
    """Q21: the one time the site unlocks for a human. What they did is kept as EVIDENCE, never as
    steps (recordable: false, so the save refuses): each page they land on (path only) and each
    send (path only, via the send guard), plus a screenshot at the start and at hand-back. The
    screenshots may show values: in memory only, redact before persisting (Q16). Returns a STUCK
    reason if a send the human started is still held long after Done, else None."""
    page = ctx.page
    started, url_before, actions = time.monotonic(), page.url, list[dict[str, str]]()
    shot_before = await snap(ctx)

    def on_page(frame: object) -> None:
        if frame == page.main_frame:
            actions.append({"kind": "page", "path": urlparse(frame.url).path})  # type: ignore[attr-defined, unused-ignore]

    ctx.run.takeover, ctx.run.dropdowns = actions, []
    stuck = await _in_control(ctx, reason, on_page)
    shot_after = await snap(ctx)
    ctx.run.typed_secrets = set()
    if not host_allowed(page.url, ctx.site):
        await page.goto(ctx.site.base_url)
    guard.log(
        ctx,
        "take_over",
        {"reason": reason},
        "handed back",
        url_before=urlparse(url_before).path,
        seconds=round(time.monotonic() - started),
        human_entry=True,
        recordable=False,
        actions=actions,
        shot_before=shot_before,
        shot_after=shot_after,
    )
    return stuck


async def _options(
    ctx: Ctx, fields: list[Field], flags: list[bool]
) -> tuple[list[list[str]], list[bool]]:
    look = ctx.run.look
    options = [
        await list_options(ctx, p) if f or element_at(look, p) else []  # type: ignore[arg-type]
        for (p, _), f in zip(fields, flags, strict=False)
    ]
    kinds = [
        f or len(o) > 1 for f, o in zip(flags, options, strict=False)
    ]  # a list that moves = a dropdown
    return [o if k else [] for o, k in zip(options, kinds, strict=False)], kinds


async def _enter(ctx: Ctx, look: Look | None, field: Field, value: str, is_dropdown: bool) -> bool:
    """Our code enters one human value and logs where (never the value), on the look taken before
    the form (``look``, as the notebook). False: not in the list."""
    point, hint = field
    index = None
    if is_dropdown:
        if (index := await choose_option(ctx, point, value)) is None:
            return False
    else:
        await act(ctx, *into_box(ctx, point, value))
    sensitive = is_sensitive(hint, ctx.session.cfg.sensitive_words)
    ctx.run.entered[hint] = "******" if sensitive else value
    if not sensitive:
        ctx.run.given.append(value)
    keep = element_at(look, point) if is_dropdown else None  # type: ignore[arg-type]
    guard.log(
        ctx,
        "request_value",
        {"hint": hint},
        "human entry",
        point,
        crop(ctx, look, point, keep),  # type: ignore[arg-type]
        human_entry=True,
        dropdown=is_dropdown,
        shapes=None if sensitive else shapes_of(value),  # names only; a sensitive one: none
        index=index,
        **where(look, point, run_values(ctx.run, ctx.secrets)),  # type: ignore[arg-type]
    )
    return True


MONEY_WORDS = ("amount", "$")  # a field label meaning "money": the goal's one amount fills it
_AMOUNT = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")


def goal_value(goal: str, label: str, options: list[str]) -> str | None:
    """The value the goal already gives for this field, or None. Code backstop for the prompt
    rule "only ask for what the goal does not give". Never a guess:
    - a dropdown: the one live option the goal names as a whole word ('#***010' -> '***010');
    - a money field: the goal's single $ amount ('$100' -> '100'); two amounts -> None."""
    if options:
        named = [o for o in options if re.search(rf"(?<![\w]){re.escape(o)}(?![\w])", goal)]
        return named[0] if len(named) == 1 else None
    if any(w in label.casefold() for w in MONEY_WORDS):
        amounts = _AMOUNT.findall(goal)
        return amounts[0].replace(",", "") if len(amounts) == 1 else None
    return None


async def human_fills(
    ctx: Ctx, fields: list[Field], dropdown: bool = False, dropdowns: list[bool] | None = None
) -> str:
    """Q16/D34/D55: the human answers in the control window's form; our code enters every value.
    The site stays locked throughout. Values are never logged and never reach the model.
    Fields the goal already gives are entered first and never put in the form."""
    look = ctx.run.look
    flags = dropdowns or [dropdown] * len(fields)
    options, kinds = await _options(ctx, fields, flags)
    fields, options, kinds, done = await _from_goal(ctx, look, fields, options, kinds)
    if not fields:
        return f"From the goal: {done}. Our code entered them. Do not type them again. Continue."
    hints = ", ".join(h for _, h in fields)
    words = ctx.session.cfg.sensitive_words
    answers = await ctx.control.form(
        f"Please fill in: {hints}",
        [(h, is_sensitive(h, words)) for _, h in fields],
        options=options,
    )
    if not answers or not any(answers):
        return f"SKIPPED: the human gave no values for {hints}."
    failed = []
    for f, value, is_dropdown in zip(fields, answers, kinds, strict=False):
        if value and not await _enter(ctx, look, f, value, is_dropdown):
            failed.append(f[1])
    if failed:
        return guard.mark_stuck(ctx, f"not in the list: {', '.join(failed)}")
    return f"A human gave: {hints}. Our code entered them. Do not type them again. Continue."


async def _from_goal(
    ctx: Ctx, look: Look | None, fields: list[Field], options: list[list[str]], kinds: list[bool]
) -> tuple[list[Field], list[list[str]], list[bool], str]:
    """Enter what the goal already gives; return only what is still the human's to fill."""
    left: tuple[list[Field], list[list[str]], list[bool]] = ([], [], [])
    done: list[str] = []
    for f, opts, kind in zip(fields, options, kinds, strict=False):
        value = goal_value(ctx.run.goal, f[1], opts)
        if value is not None and await _enter(ctx, look, f, value, kind):
            done.append(f[1])
            continue
        for bucket, item in zip(left, (f, opts, kind), strict=False):
            bucket.append(item)  # type: ignore[attr-defined]
    return left[0], left[1], left[2], ", ".join(done)


def start_page_refusal(ctx: Ctx) -> str | None:
    """D34, generic: asking for form values on the page the run began on is too early."""
    if urlparse(ctx.page.url).path.split(";")[0] == urlparse(ctx.site.start_url).path:
        return "NOT YET: you are on the start page. Open the page where the task is done first."
    return None


def _make_finish(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @guard.one_at_a_time(ctx)
    async def finish_business_outcome(outcome: str, proof_text: str) -> guard.Result:
        """Report the business result, with text on the screen that proves it.

        Args:
            outcome: The result in plain words.
            proof_text: Exact text visible on the screen that proves it.
        """
        if norm(proof_text) not in norm(ctx.run.look.text if ctx.run.look else ""):
            return "REFUSED: that proof text is not on the screen. Observe and copy it exactly."
        args: dict[str, object] = {"outcome": outcome, "proof_text": proof_text}
        guard.log(ctx, "finish_business_outcome", args, "OK")
        return "OK"

    return finish_business_outcome


def _make_request_missing_values(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @guard.one_at_a_time(ctx)
    async def request_missing_values(fields: list[dict[str, int | str]]) -> guard.Result:
        """Hand a human every field on this page the goal gives no value for (boxes and dropdowns).

        Args:
            fields: One entry per field: {"x": int, "y": int, "hint": "label you read",
                "dropdown": true if it is a dropdown (a box with a small arrow)}. For a dropdown,
                give x,y of the box itself, not its label.
        """
        if refusal := start_page_refusal(ctx):
            return await observe.reply(ctx, refusal)
        points = [
            (guard.resolve_point(ctx, None, int(f["x"]), int(f["y"])), str(f["hint"]))
            for f in fields
        ]
        if bad := next((p for p, _ in points if isinstance(p, str)), None):
            return await observe.reply(ctx, bad)
        flags = [bool(f.get("dropdown")) for f in fields]
        msg = await human_fills(ctx, points, dropdowns=flags) if points else "No fields given."  # type: ignore[arg-type]
        return await observe.reply(ctx, msg)

    return request_missing_values


def _make_ask_human(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @guard.one_at_a_time(ctx)
    async def ask_human(question: str) -> guard.Result:
        """Ask a human whenever you are unsure: what to do, which option, what the goal means.

        Args:
            question: What you are unsure about, and what you see.
        """
        return await human_help(ctx, "The agent asks", question)

    return ask_human


def make_human_tools(ctx: Ctx) -> list[BaseTool]:
    """finish_business_outcome, request_missing_values, ask_human (the notebook's TOOLS order)."""
    return [_make_finish(ctx), _make_request_missing_values(ctx), _make_ask_human(ctx)]

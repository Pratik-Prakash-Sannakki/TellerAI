"""The tools that act on the page: click, type_text, type_secret, select_option.

Moved from discovery.py 1145-1295 (landed, click, type_text, type_secret, select_option). Globals
become ``ctx``: site words from ``ctx.site``, sizes from ``ctx.session.cfg``. ``click`` (44 lines)
is split into ``_press`` (the click itself and its result) and ``_landing`` (the event's
navigation fields); type_text/type_secret/select_option keep their checks and hand the rest to
``_typed``/``_secret_typed``/``_selected``. Bodies otherwise unchanged. Tool names, signatures
and docstrings are the notebook's: the model reads them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.tools import BaseTool, tool

from cua.discovery.context import Ctx, act, canvas, choose_option, crop, into_box, look, to_page
from cua.discovery.recorder.types import shapes_of
from cua.discovery.run import run_values
from cua.discovery.tools.guard import (
    Result,
    after_login_click,
    gate_click,
    log,
    mark_stuck,
    needs_human_value,
    one_at_a_time,
    resolve_point,
)
from cua.discovery.tools.human import human_fills
from cua.discovery.tools.observe import blocks, reply
from cua.discovery.tools.read_helpers import Spot, label_near, page_texts, where
from cua.safety import host_allowed, is_sensitive, norm
from cua.vision.crops import element_at, read_near, screens_same, typed_into_box
from cua.vision.look import Look


@dataclass(frozen=True)
class _Target:
    """What a click aims at, worked out before it happens."""

    point: tuple[int, int]
    text: str | None
    args: dict[str, object]
    crop: bytes
    spots: Spot


def landed(ctx: Ctx, before: Look, after: Look) -> list[str]:
    """Text the page showed in response to a send: the replay checkpoint. Fixed page text only:
    nothing with a digit (amounts, account numbers) and nothing the human or the goal gave."""
    run = ctx.run
    old, given = norm(before.text), [norm(v) for v in (*run.given, *run.typed_texts) if norm(v)]
    return [
        e.text
        for e in after.elements
        if norm(e.text)
        and norm(e.text) not in old
        and re.search(r"[^\W\d_]", e.text)
        and not re.search(r"\d", e.text)
        and not any(v in norm(e.text) for v in given)
    ]


def _landing(ctx: Ctx, before: Look, after: Look, navs: int, sent: bool) -> dict[str, object]:
    """The click event's fields after the click: where it came from and what it led to."""
    return {
        "from_texts": page_texts(before, run_values(ctx.run, ctx.secrets)),
        "from_url": before.url,
        "loaded": ctx.page.url != before.url,
        "navigated": ctx.run.navs != navs,
        "new_texts": bool(
            {norm(e.text) for e in after.elements} - {norm(e.text) for e in before.elements}
        ),
        **({"landed": landed(ctx, before, after)} if sent else {}),
    }


async def _press(ctx: Ctx, before: Look, t: _Target) -> Result:
    """The click itself (login clicks may send), then what it did, logged."""
    page, cfg, login = ctx.page, ctx.session.cfg, norm(t.text) in ctx.site.login_words
    ctx.run.allow_send, navs = login, ctx.run.navs
    try:
        after = await act(ctx, lambda: page.mouse.click(*to_page(ctx, t.point)))
    finally:
        ctx.run.allow_send = False
    msg, sent = f"Clicked {t.text or t.point!r}.", ctx.run.verdict.startswith("SENT")
    if page.url != before.url:
        ctx.run.entered = {}
    if not host_allowed(page.url, ctx.site):
        await page.go_back()
        after, msg = await look(ctx), "BLOCKED: left the allowed site. Went back."
    elif screens_same(before.png, after.png, cfg) and not sent:  # a send that went out is a step
        msg = f"NO CHANGE after clicking {t.point}. Look again and retry."
    if login:
        ctx.run.typed_secrets.clear()
        msg = after_login_click(ctx, after.text) or msg
    log(
        ctx,
        "click",
        t.args,
        msg,
        t.point,
        t.crop,
        text=t.text,
        **t.spots,
        login=login,
        **_landing(ctx, before, after, navs, sent),
    )
    return blocks(ctx, msg, after)


def _make_click(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def click(ref: int | None = None, x: int | None = None, y: int | None = None) -> Result:
        """Click a numbered box, or a spot with no number by x,y. Risky clicks ask a human first.

        Args:
            ref: Number of the box in the latest look.
            x: Pixel x of a spot with no number.
            y: Pixel y of a spot with no number.
        """
        point = resolve_point(ctx, ref, x, y)
        if isinstance(point, str):
            return await reply(ctx, point)
        before = ctx.run.look
        assert before is not None  # resolve_point refused a missing look
        el = element_at(before, point)
        text, cut = (el.text if el else None), crop(ctx, before, point, el)
        args: dict[str, object] = {"ref": ref, "x": x, "y": y}
        typed = (*ctx.secrets.values(), *ctx.run.typed_texts)
        if text and any(norm(v) and norm(v) in norm(text) for v in typed):
            msg = (
                "REFUSED: that number is text inside a box you already filled. It is done; move on."
            )
            log(ctx, "click", args, msg, point, cut)
            return blocks(ctx, msg, before)
        spots = where(before, point, run_values(ctx.run, ctx.secrets), own=el)
        if refusal := await gate_click(ctx, text, cut):
            log(ctx, "click", args, refusal, point, cut, text=text, **spots)
            return blocks(ctx, refusal, before)
        return await _press(ctx, before, _Target(point, text, args, cut, spots))

    return click


async def _typed(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, lk: Look, point: tuple[int, int], hint: str, text: str, args: dict[str, object]
) -> Result:
    """type_text's body once the value is the agent's to type: type it, read the box back, log."""
    cut, spots = crop(ctx, lk, point, None), where(lk, point, run_values(ctx.run, ctx.secrets))
    after = await act(ctx, *into_box(ctx, point, text))
    ctx.run.typed_texts.add(text)
    shown = read_near(after, point, canvas(ctx), ctx.session.cfg)
    msg = (
        f"Typed at {point}. Box shows {shown!r}."
        if norm(text) in norm(shown)
        else f"TYPED at {point} but the box shows {shown!r}. Look again."
    )
    ctx.run.entered[hint] = text
    shapes = shapes_of(text)  # the value's shape names only: the recorder types the input
    log(ctx, "type_text", args, msg.split(" Box shows")[0], point, cut, shapes=shapes, **spots)
    return blocks(ctx, msg, after)


async def _selected(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, lk: Look, point: tuple[int, int], hint: str, option: str, args: dict[str, object]
) -> Result:
    """select_option's body once the option is the agent's to pick: choose it, log its index."""
    own = element_at(lk, point)
    cut, spots = crop(ctx, lk, point, own), where(lk, point, run_values(ctx.run, ctx.secrets))
    if (index := await choose_option(ctx, point, option)) is None:
        return await reply(ctx, mark_stuck(ctx, f"'{option}' is not an option in '{hint}'"))
    msg = f"Selected '{option}' at {point}."
    ctx.run.entered[hint] = option
    shapes = shapes_of(option)  # names only, never the option
    log(ctx, "select_option", args, "Selected.", point, cut, index=index, shapes=shapes, **spots)
    return await reply(ctx, msg)


def _make_type_text(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def type_text(
        text: str, ref: int | None = None, x: int | None = None, y: int | None = None
    ) -> Result:
        """Click a box (by number or x,y) and type text. Only values from the user's goal.

        Args:
            text: The text to type. It must come from the goal.
            ref: Number of a box, or leave empty and give x and y.
            x: Pixel x of an empty input box.
            y: Pixel y of an empty input box.
        """
        point = resolve_point(ctx, ref, x, y)
        if isinstance(point, str):
            return await reply(ctx, point)
        lk = ctx.run.look
        assert lk is not None  # resolve_point refused a missing look
        label = label_near(lk, point, run_values(ctx.run, ctx.secrets))
        hint = label.text if label else "value"
        if needs_human_value(ctx, text, hint):
            return await reply(ctx, await human_fills(ctx, [(point, hint)]))
        return await _typed(ctx, lk, point, hint, text, {"ref": ref, "x": x, "y": y})

    return type_text


async def _secret_typed(ctx: Ctx, name: str, point: tuple[int, int]) -> Result:
    """Type the secret into the box at the point; never show it (type_secret's body after the
    checks)."""
    before, cfg = ctx.run.look, ctx.session.cfg
    assert before is not None  # resolve_point refused a missing look
    cut, spots = crop(ctx, before, point, None), where(
        before, point, run_values(ctx.run, ctx.secrets)
    )
    after = await act(ctx, *into_box(ctx, point, ctx.secrets[name]))
    if is_sensitive(name, cfg.sensitive_words) and ctx.secrets[name] in read_near(
        after, point, canvas(ctx), cfg
    ):
        ctx.run.look = None
        log(ctx, "type_secret", {"secret_name": name}, "STOP: secret visible", point, cut, **spots)
        return "STOP: the box shows the secret as plain text. Call ask_human; do not observe."
    if typed := typed_into_box(before, after, point, canvas(ctx), cfg):  # ink inside the box
        ctx.run.typed_secrets.add(name)
    msg = (
        f"Typed secret '{name}' at {point}."
        if typed
        else f"NOTHING TYPED at {point}: that point is not an input box. Point at the empty "
        "box itself (usually right of or below its label) and try once more."
    )
    log(ctx, "type_secret", {"secret_name": name}, msg, point, cut, **spots)
    return blocks(ctx, msg, after)


def _make_type_secret(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def type_secret(
        name: str, ref: int | None = None, x: int | None = None, y: int | None = None
    ) -> Result:
        """Click a box and type a stored secret. You give only its name and never see the value.

        Args:
            name: The secret's name.
            ref: Number of a box, or leave empty and give x and y.
            x: Pixel x of an empty input box.
            y: Pixel y of an empty input box.
        """
        if not ctx.secrets.get(name):
            return await reply(ctx, f"UNKNOWN SECRET '{name}'. Use one of: {sorted(ctx.secrets)}")
        if not host_allowed(ctx.page.url, ctx.site):
            return await reply(ctx, "REFUSED: this site is not on the allowlist.")
        point = resolve_point(ctx, ref, x, y)
        if isinstance(point, str):
            return await reply(ctx, point)
        return await _secret_typed(ctx, name, point)

    return type_secret


def _make_select_option(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def select_option(
        option: str, ref: int | None = None, x: int | None = None, y: int | None = None
    ) -> Result:
        """Pick the dropdown option that matches. Nothing is typed. Give option="" if the goal does not name it.

        Args:
            option: Visible option text from the goal, or "" to let a human choose.
            ref: Number of the dropdown, or leave empty and give x and y.
            x: Pixel x of the dropdown.
            y: Pixel y of the dropdown.
        """  # noqa: E501 (the model reads this docstring verbatim)
        point = resolve_point(ctx, ref, x, y)
        if isinstance(point, str):
            return await reply(ctx, point)
        lk = ctx.run.look
        assert lk is not None  # resolve_point refused a missing look
        label = label_near(lk, point, run_values(ctx.run, ctx.secrets))
        hint = label.text if label else "option"
        if needs_human_value(ctx, option, hint):
            return await reply(ctx, await human_fills(ctx, [(point, hint)], dropdown=True))
        return await _selected(ctx, lk, point, hint, option, {"ref": ref, "x": x, "y": y})

    return select_option


def make_act_tools(ctx: Ctx) -> list[BaseTool]:
    """click, type_text, type_secret, select_option (the notebook's TOOLS order)."""
    return [
        _make_click(ctx),
        _make_type_text(ctx),
        _make_type_secret(ctx),
        _make_select_option(ctx),
    ]

"""One function per action. Each acts through :func:`cua.replay.wiring.act` and returns whether
its OCR check passed. ``find`` (all rungs miss -> scroll, retry) lives here: it scrolls the page.

Moved from notebooks/replay/replay.py: ``field_box``/``read_field``/``shows_option``/
``choose_option`` (674-705), ``find`` (954-960), ``shows`` ... ``ACTIONS`` (968-1246; the table
reader itself is ``cua.vision.table``). Bodies unchanged; globals -> ``ctx`` (first parameter):
``STATE`` -> ``ctx.run``, ``CFG`` -> ``ctx.cfg``/``ctx.bcfg``, ``SECRETS`` -> ``ctx.secrets``,
``SEND_GATE`` -> ``ctx.guard.lock``, ``page`` -> ``ctx.page``. ``is_type`` is the shared
``cua.schema.value_matches_type`` (same body, same TYPES).
"""

from __future__ import annotations

import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from urllib.parse import urljoin

import cv2

from cua.browser.dropdown import SELECT_AT_INDEX_JS, choose_option_at_index
from cua.browser.input import into_box
from cua.replay.context import Ctx
from cua.replay.loader import PLACEHOLDER, ask_option, fill, secret_name
from cua.replay.locate import locate, same_label, same_text, typed_ok
from cua.replay.wiring import act, canvas, look, stash_dropdowns, to_page
from cua.safety.hosts import host_allowed
from cua.safety.redact import hide_secrets, is_sensitive, norm
from cua.schema import Capability, Step, Stop, Target, value_matches_type
from cua.vision import (
    Box,
    Look,
    append_rows,
    crop_box,
    decode,
    element_at,
    read_rows,
    screens_same,
    spot_changed,
    table_columns,
    typed_into_box,
)

Point = tuple[int, int]
Action = Callable[[Ctx, Step, Point, Capability], Awaitable[bool]]
is_type = value_matches_type
RUNGS = {"table": "table_cell", "rung1": "ocr_text", "rung2": "anchor", "rung3": "template"}


def field_box(ctx: Ctx, look: Look, point: Point) -> Box:
    """The smallest drawn rectangle around the point (the input's own border), else the point
    crop."""
    edges = cv2.Canny(cv2.cvtColor(decode(look.png), cv2.COLOR_BGR2GRAY), 30, 90)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(c) for c in contours]
    fw, fh = ctx.cfg.field_min
    boxes = [Box(x, y, x + w, y + h) for x, y, w, h in rects if w >= fw and h >= fh]
    hits = [b for b in boxes if b.contains(*point)]
    if hits:
        return min(hits, key=lambda b: (b.x2 - b.x1) * (b.y2 - b.y1))
    return crop_box(point, None, canvas(ctx), ctx.bcfg)


def read_field(ctx: Ctx, look: Look, point: Point) -> str:
    """Text inside the whole field: short values sit at its left edge, not near the centre
    (bug A)."""
    b = field_box(ctx, look, point)
    return " ".join(e.text for e in look.elements if e.box.overlaps(b))


def shows_option(ctx: Ctx, seen: str, option: str) -> bool:
    """The option is in the box's OCR, even merged with its label ('to account #|15120'): the
    option's own words, whole. Box borders read as `[ ] |` are cut first."""
    return typed_ok(re.sub(r"[\[\]|#]", " ", seen), option, ctx.cfg)


async def choose_option(ctx: Ctx, point: Point, option: str, index: int | None = None) -> bool:
    """Select this exact live option in the Nth <select> (`index`), else the one at the point;
    the dropdown's selected text and its OCR'd box confirm it."""
    return await choose_option_at_index(
        ctx.session,
        to_page(ctx, point),
        option,
        index,
        look_fn=lambda: look(ctx),
        confirm=lambda lk, p, opt: shows_option(ctx, read_field(ctx, lk, p), opt),
    )


async def find(ctx: Ctx, target: Target, crops: Path | None) -> tuple[Point, str] | None:
    """All rungs miss -> scroll down and try again (Q13), up to `scroll_retries`."""
    for n in range(ctx.cfg.scroll_retries + 1):
        lk = (
            ctx.run.look
            if n == 0
            else await act(ctx, lambda: ctx.page.mouse.wheel(0, ctx.bcfg.scroll_px))
        )
        if hit := locate(lk, target, ctx.run.values, crops, ctx.cfg):  # type: ignore[arg-type]
            return hit if n == 0 else (hit[0], f"{hit[1]}+scroll{n}")
    return None


async def shows(ctx: Ctx, text: str) -> bool:
    """R5: bounded OCR poll until the text is on screen."""
    deadline = time.monotonic() + ctx.cfg.check_s
    while norm(fill(text, ctx.run.values)) not in norm(ctx.run.look.text):  # type: ignore[union-attr]
        if time.monotonic() > deadline:
            return False
        await ctx.page.wait_for_timeout(ctx.cfg.poll_ms)
        await look(ctx)
    return True


def site_url(base_url: str, path: str) -> str:
    """Like a browser: '/app/x.htm' is from the site root, 'x.htm' is under base_url."""
    return urljoin(base_url + "/", path)


async def do_navigate(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    url = site_url(cap.base_url, fill(step.path, ctx.run.values))  # type: ignore[union-attr]
    if not host_allowed(url, ctx.site):
        raise Stop("FAILED", "navigate leaves the allowed site")
    await ctx.page.goto(url)
    await look(ctx)
    return True


async def do_click(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    run = ctx.run
    before, navs = run.look, run.navs
    el = element_at(before, point)  # type: ignore[arg-type]
    run.allow_send = norm(el.text if el else "") in ctx.site.login_words  # R6: login is exempt
    await stash_dropdowns(ctx)
    try:
        await act(ctx, lambda: ctx.page.mouse.click(*to_page(ctx, point)))
    finally:
        run.allow_send = False
    if not host_allowed(ctx.page.url, ctx.site):
        await ctx.page.go_back()
        raise Stop("FAILED", "the click left the allowed site")
    if run.navs > navs:  # the page loaded again (even the same URL, the same screen)
        return True
    return await settled_change(ctx, before)  # type: ignore[arg-type]


def changed(ctx: Ctx, before: Look, after: Look) -> bool:
    """The pixels moved, or new text is on screen: a small answer ('Transfer Complete!') can sit
    under the whole-screen pixel threshold, but OCR still sees it."""
    return not screens_same(before.png, after.png, ctx.bcfg) or norm(before.text) != norm(
        after.text
    )


async def settled_change(ctx: Ctx, before: Look) -> bool:
    """Bug D: a send can land after the settle. Poll until the screen changes, then holds still.
    A send held at the gates is never judged: the window starts again once the human answered."""
    deadline, prev = time.monotonic() + ctx.cfg.check_s, ctx.run.look
    while time.monotonic() < deadline:
        await ctx.page.wait_for_timeout(ctx.cfg.poll_ms)
        if ctx.guard.lock.locked():  # the gates took the send after `act`'s own wait
            async with ctx.guard.lock:
                pass
            deadline = time.monotonic() + ctx.cfg.check_s
        lk = await look(ctx)
        if changed(ctx, before, lk) and not changed(ctx, prev, lk):  # type: ignore[arg-type]
            return True
        prev = lk
    return changed(ctx, before, ctx.run.look)  # type: ignore[arg-type]


async def do_type(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    before, name = ctx.run.look, secret_name(step.value)  # type: ignore[union-attr]
    value = ctx.secrets[name] if name else fill(step.value, ctx.run.values)  # type: ignore[union-attr]
    after = await act(ctx, *into_box(ctx.page, ctx.run.look, point, value))
    size = canvas(ctx)
    if not name:  # OCR misses a lone character ('1'): then the field's own pixels must change
        short = len(value.strip()) <= ctx.cfg.short_value
        typed = typed_ok(read_field(ctx, after, point), value, ctx.cfg)
        return typed or short and spot_changed(before, after, point, size, ctx.bcfg)  # type: ignore[arg-type]
    if is_sensitive(name, ctx.bcfg.sensitive_words) and value in read_field(ctx, after, point):
        ctx.run.look = None
        raise Stop("FAILED", f"secret '{name}' shows as plain text")
    return typed_into_box(before, after, point, size, ctx.bcfg)  # type: ignore[arg-type]


async def do_select(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    js_args = [*to_page(ctx, point), None, step.index]  # type: ignore[union-attr]
    options = await ctx.page.evaluate(SELECT_AT_INDEX_JS, js_args)
    if not isinstance(options, list) or not options:
        return False
    m = PLACEHOLDER.fullmatch(step.option.strip())  # type: ignore[union-attr]
    want = ctx.run.values.get(m[2], "") if m else step.option  # type: ignore[union-attr]
    if m and want not in options:
        want = ctx.run.values[m[2]] = await ask_option(ctx, cap, m[2], options)
        ctx.run.given.append(want)
    return await choose_option(ctx, point, want, step.index)  # type: ignore[union-attr]


async def do_scroll(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    px = ctx.bcfg.scroll_px if step.direction == "down" else -ctx.bcfg.scroll_px  # type: ignore[union-attr]
    await act(ctx, lambda: ctx.page.mouse.wheel(0, px))
    return True


def next_rung(ctx: Ctx, target: Target, rung: str) -> tuple[Point, str] | None:
    """Where the rungs after `rung` point (e.g. the anchor after a wrong table cell), if any."""
    order = list(RUNGS.values())
    base = rung.split("+")[0]
    done = order[: order.index(RUNGS[base]) + 1] if base in RUNGS else order
    rest = target.model_copy(update=dict.fromkeys(done))
    if not any(getattr(rest, k) for k in order):
        return None
    return locate(ctx.run.look, rest, ctx.run.values, None, ctx.cfg)  # type: ignore[arg-type]


def value_of(text: str, kind: str, pattern: str | None) -> str | None:
    """The box's value: with a saved `pattern`, its first match inside the box; else the whole
    box. Either way it must be the output's type."""
    if pattern:
        hit = re.search(pattern, text)
        text = hit.group() if hit else ""
    return text.strip() if is_type(text, kind) else None


async def do_extract(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    """Read the value at the point. A wrong value tries the next rung once, then stops: never
    guess."""
    run, save_as = ctx.run, step.save_as  # type: ignore[union-attr]
    kind = next(o.type for o in cap.outputs if o.name == save_as)
    pattern = getattr(step, "pattern", None)  # optional: older artifacts have none
    el = element_at(run.look, point)  # type: ignore[arg-type]
    if (
        el
        and value_of(el.text, kind, pattern) is None
        and (hit := next_rung(ctx, step.target, run.rung))  # type: ignore[union-attr]
    ):
        el, run.rung = element_at(run.look, hit[0]) or el, hit[1]  # type: ignore[arg-type]
    if el is None:
        return False
    if (value := value_of(el.text, kind, pattern)) is None:
        raise Stop("STUCK", f"{save_as} is not a {kind}", kind, hide_secrets(el.text, ctx.secrets))
    run.outputs[save_as] = value
    return True


async def do_extract_table(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    """Find the header by its label (rung 2's matching), read the rows with discovery's own
    reader, and scroll on while the table runs past the screen, up to `row_limit`. No rows is a
    valid output ([]); a header not on screen is a failed check."""
    run, limit = ctx.run, step.row_limit  # type: ignore[union-attr]
    header = step.header  # type: ignore[union-attr]
    label, look = fill(header.label, run.values), run.look
    # Only label hits whose line holds every asked column count: discovery's ordinal is over
    # exact header texts, and a menu's 'Account Services' only starts with 'Account'.
    hits = [
        found
        for e in look.elements  # type: ignore[union-attr]
        if same_label(e.text, label, ctx.cfg)
        and (found := table_columns(look, e, step.columns, lambda a, b: same_text(a, b, ctx.cfg)))  # type: ignore[union-attr, arg-type]
    ]
    if len(hits) < header.ordinal:
        return False
    cols, below = hits[header.ordinal - 1]
    rows, more = read_rows(run.look, cols, below, limit)  # type: ignore[arg-type]
    while more and len(rows) < limit:
        await act(ctx, lambda: ctx.page.mouse.wheel(0, ctx.bcfg.scroll_px))
        new, more = read_rows(run.look, cols, None, limit)  # type: ignore[arg-type]
        if len(grown := append_rows(rows, new)[:limit]) == len(rows):
            break  # the scroll showed nothing new: the table's end
        rows = grown
    run.outputs[step.save_as] = rows  # type: ignore[union-attr]
    return True


async def do_extract_options(ctx: Ctx, step: Step, point: Point, cap: Capability) -> bool:
    """Read the live options of the dropdown found like a select (its recorded index, else the
    point) through the dropdown exception; the list is the output. No dropdown there: the check
    fails. Never selects anything."""
    js_args = [*to_page(ctx, point), None, step.index]  # type: ignore[union-attr]
    options = await ctx.page.evaluate(SELECT_AT_INDEX_JS, js_args)
    if not isinstance(options, list):
        return False
    ctx.run.outputs[step.save_as] = [hide_secrets(str(o), ctx.secrets) for o in options]  # type: ignore[union-attr]
    return True


ACTIONS: dict[str, Action] = {
    "navigate": do_navigate,
    "click": do_click,
    "type": do_type,
    "select": do_select,
    "scroll": do_scroll,
    "extract": do_extract,
    "extract_table": do_extract_table,
    "extract_options": do_extract_options,
}

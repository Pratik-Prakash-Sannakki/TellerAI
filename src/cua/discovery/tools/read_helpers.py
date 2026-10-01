"""Where a point is on a look, in words: labels, anchors, page texts. Pure (no page).

Moved from discovery.py 320-371 (clean_label, label_near, spot, merged_label, where) and
1457-1534 (is_word, column_header, row_block, table_cell, read_target, headings, page_texts),
1554-1565 (value_in_box, on cua.schema.value_types) and 1594-1603 (is_header, off_table). The
notebook read ``run_values()`` inside; here the run's values are an explicit ``values``
(``run_values(ctx.run, ctx.secrets)``) parameter.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace

from cua.safety.redact import norm, redactor
from cua.schema.value_types import SHAPES, value_matches_type
from cua.vision.crops import element_at
from cua.vision.look import Element, Look
from cua.vision.table import TABLE_GAP

Spot = dict[str, object]


def clean_label(text: str, values: set[str]) -> str:
    """OCR joins a label to the box beside it ('to account #16785') and reads a box border as '['
    or '|'. Both are cut. '' when no word is left: then it is no label at all (a value, a number).
    """
    left = " ".join(redactor(values, " ")(re.sub(r"[\[\]|]", " ", text)).split())
    return left if re.search(r"[^\W\d_]", left) else ""


def label_near(
    look: Look,
    point: tuple[int, int],
    avoid: set[str],
    radius: int = 250,
    skip: Element | None = None,
) -> Element | None:
    """The text above/left of the point that labels it, cleaned (clean_label): never a value
    typed, entered, given or sent this run (``avoid``). A label on the point's own row, to its
    left, wins (a wide form); else the nearest (a label above its box). Returned with its cleaned
    text."""
    px, py = point

    def dist(e: Element) -> int:
        return abs(e.box.center[0] - px) + abs(e.box.center[1] - py)

    near = [
        replace(e, text=t)
        for e in look.elements
        if e is not skip
        and e.box.x1 <= px
        and e.box.y1 <= py
        and dist(e) <= radius
        and (t := clean_label(e.text, avoid))
    ]
    same_row = [e for e in near if e.box.y1 <= py <= e.box.y2 and e.box.x2 <= px]
    return min(same_row or near, key=dist, default=None)


def spot(look: Look, el: Element, text: Callable[[str], str] = lambda t: t) -> Spot:
    """Text, box, and ordinal (the Nth element on screen whose `text(...)` is the same), for
    replay's rungs."""
    same = [e.ref for e in look.elements if norm(text(e.text)) == norm(el.text)]
    return {
        "text": el.text,
        "box": [el.box.x1, el.box.y1, el.box.x2, el.box.y2],
        "ordinal": same.index(el.ref) + 1,
    }


def merged_label(el: Element | None, values: set[str]) -> Element | None:
    """The box under the point, when OCR merged a label with this run's value in it ('to account
    #|15120'): its cleaned label is the field's own. A box with no value cut from it is not one."""
    if el is None or redactor(values, " ")(el.text) == el.text:
        return None
    return replace(el, text=t) if (t := clean_label(el.text, values)) else None


def where(look: Look, point: tuple[int, int], values: set[str], own: Element | None = None) -> Spot:
    """R14: anchor label + offset (rung 2) and the clicked element (rung 1). The text under the
    point is never the anchor (in a box it could be a value), except a label merged with a value."""
    under = element_at(look, point)
    label = merged_label(under, values) or label_near(look, point, values, skip=under)
    if label is None:
        return {"own": spot(look, own) if own else None}
    cx, cy = label.box.center
    return {
        "own": spot(look, own) if own else None,
        "anchor": spot(look, label, lambda t: clean_label(t, values)),
        "label": label.text,
        "offset": [point[0] - cx, point[1] - cy],
    }


def is_word(text: str, values: set[str]) -> bool:
    """A header or row key: has a letter and holds no run value (an account number never is)."""
    return bool(re.search(r"[^\W\d_]", text)) and redactor(values)(text) == text


def headings(look: Look, values: set[str], skip: Element | None = None) -> list[str]:
    """The look's words, tallest text first (a page heading is its biggest text)."""
    words = [e for e in look.elements if e.text in page_texts(look, values, skip)]
    return [e.text for e in sorted(words, key=lambda e: -(e.box.y2 - e.box.y1))][:5]


def page_texts(look: Look, values: set[str], skip: Element | None = None) -> list[str]:
    """The words on a look (never a value: letters, no run value in them), to pick a read-only
    run's checkpoint from later. flag_leaks drops any that turn out to hold a value."""
    redact = redactor(values)
    return [
        e.text
        for e in look.elements
        if e is not skip and re.search(r"[^\W\d_]", e.text) and redact(e.text) == e.text
    ][:60]


KEY_REACH = 600  # px: a row key further left than this is not the value's own row key


def column_header(look: Look, el: Element, values: set[str]) -> Element | None:
    """The value's column, walked upwards while each text is within TABLE_GAP of the one below and
    aligned with the value (one's centre inside the other's span): its topmost text, if it is a
    word on a line with 2+ texts (a header row). A menu or title beside the column is not in it."""

    def aligned(e: Element) -> bool:
        return e.box.x1 <= el.box.center[0] <= e.box.x2 or el.box.x1 <= e.box.center[0] <= el.box.x2

    top, header = el, None
    for e in sorted(
        (e for e in look.elements if e.box.y2 <= el.box.y1 and aligned(e)), key=lambda e: -e.box.y2
    ):
        if top.box.y1 - e.box.y2 >= TABLE_GAP:
            break
        top = e
    if top is not el and is_word(top.text, values):
        header = top
    line = [
        e for e in look.elements if header and e.box.y1 < header.box.y2 and header.box.y1 < e.box.y2
    ]
    return header if len(line) >= 2 else None  # noqa: PLR2004


def row_block(look: Look, el: Element) -> list[Element] | None:
    """The texts on el's row, left of it, up to its table's left edge: the first CLEAR gap (1.5x
    every gap before it). None when no such edge is found among 2+ texts: a side menu as far away
    as the next column looks like one more column, so it is unsure."""
    row = sorted(
        (
            e
            for e in look.elements
            if e.box.y1 < el.box.y2 and el.box.y1 < e.box.y2 and e.box.x2 <= el.box.x1
        ),
        key=lambda e: -e.box.x2,
    )
    edges = [el.box.x1, *(e.box.x1 for e in row)]
    gaps = [edges[i] - e.box.x2 for i, e in enumerate(row)]
    cut = next((i for i in range(1, len(gaps)) if gaps[i] >= 1.5 * max(gaps[:i])), None)
    if cut is None and len(row) > 1:
        return None
    return row[:cut]


def table_cell(look: Look, el: Element, values: set[str]) -> dict[str, str] | None:
    """Row key + column header, only for a value in a real table, else None (replay then uses the
    anchor). The row key is the left-most text of the value's own table block (row_block): a word,
    not a value, within KEY_REACH, under a text of the header line."""
    header, block = column_header(look, el, values), row_block(look, el)
    if header is None or not block:
        return None
    key = block[-1]
    heads = [
        h
        for h in look.elements
        if h is not header and h.box.y1 < header.box.y2 and header.box.y1 < h.box.y2
    ]
    if (
        el.box.x1 - key.box.x1 > KEY_REACH
        or not is_word(key.text, values)
        or not any(h.box.x1 < key.box.x2 and key.box.x1 < h.box.x2 for h in heads)
    ):
        return None
    return {"row_key": key.text, "column": header.text}


def read_target(look: Look, el: Element, values: set[str]) -> Spot:
    """Where an extracted value is, for replay, never the value itself: its table cell when it
    clearly sits in one; its anchor is its column header (+ offset) when it has one, else the
    nearest label. A row's left-most text may be a menu link, so it is never the anchor."""
    header = column_header(look, el, values)
    if header is None:
        return {"table": table_cell(look, el, values), **where(look, el.box.center, values)}
    (hx, hy), (px, py) = header.box.center, el.box.center
    return {
        "table": table_cell(look, el, values),
        "own": None,
        "label": header.text,
        "anchor": spot(look, header, lambda t: clean_label(t, values)),
        "offset": [px - hx, py - hy],
    }


def value_in_box(text: str, value_type: str) -> tuple[str, str | None] | None:
    """(value, pattern) for an extract: the whole box when it is exactly the type, else the first
    match of the type's shape inside it ('www.x.com or call 888-305-0041' -> the phone), with that
    shape saved so replay cuts it the same way. None when the box does not hold one."""
    shape = SHAPES.get(value_type)
    if shape is None:
        return (text, None) if value_matches_type(text, value_type) else None
    if re.fullmatch(shape, text.strip()):
        return text.strip(), None
    hit = re.search(shape, text)
    return (hit.group(), shape) if hit else None


def is_header(seen: str, want: str) -> bool:
    return norm(seen) == norm(want)


def off_table(look: Look, rows: list[dict[str, str]]) -> Look:
    """The look without the table's cells: its page texts and headings pick the checkpoint, and a
    cell is a value, never a checkpoint."""
    cells = {t for r in rows for t in r.values()}
    return replace(
        look,
        elements=tuple(
            e for e in look.elements if e.text not in cells and not any(e.text in c for c in cells)
        ),
    )

"""Where a point is on a look, in words: labels, anchors, page texts. Pure (no page).

Moved from discovery.py 320-371 (clean_label, label_near, spot, merged_label, where) and
1457-1534 (is_word, headings, page_texts). The notebook read ``run_values()`` inside; here the
run's values are an explicit ``values`` (``run_values(ctx.run, ctx.secrets)``) parameter.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace

from cua.safety.redact import norm, redactor
from cua.vision.crops import element_at
from cua.vision.look import Element, Look

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

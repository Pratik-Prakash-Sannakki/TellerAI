"""Event-log filters: which logged tool calls become steps (R16), plus the field/leak helpers.

Moved unchanged from notebooks/discovery/discovery.py (the "Save artifact" cells, and
FIELD_GAP/is_select/field_area/same_spot and flag_leaks from earlier cells). Pure: event dicts in,
event dicts out. Labels, points and crops only, never a typed value.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from cua.discovery.tools.failed import FAILED
from cua.safety.redact import norm, redactor
from cua.schema import Event

FIELD_TOOLS = {"type_text", "type_secret", "select_option", "request_value"}
READ_TOOLS = {"extract_value", "extract_table"}
STEP_TOOLS = FIELD_TOOLS | READ_TOOLS | {"click", "scroll", "open_path"}
LOGOUT_WORDS = {"log out", "logout", "sign out", "sign off"}
FIELD_GAP = (40, 12)  # a dropdown is wide and short: points this close (x, y) are the same one


def is_select(ev: Event) -> bool:
    return ev["tool"] == "select_option" or (
        ev["tool"] == "request_value" and bool(ev.get("dropdown"))
    )


def field_area(ev: Event) -> tuple[int, int, int, int]:
    """The field's own box when known (a sent dropdown), else a wide, short box around the point."""
    if ev.get("field_box"):
        return tuple(ev["field_box"])  # type: ignore[arg-type,return-value]
    (x, y), (dx, dy) = ev["point"], FIELD_GAP  # type: ignore[misc]
    return x - dx, y - dy, x + dx, y + dy


def same_spot(a: Event, b: Event) -> bool:
    """Two events on one field: same page, one's point inside the other's area. Position, not the
    label: OCR reads one label two ways ('From account #[' and 'From account #')."""
    inside = lambda p, r: r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]  # noqa: E731
    return (
        urlparse(a["url"]).path == urlparse(b["url"]).path
        and a["point"] is not None
        and b["point"] is not None
        and (inside(a["point"], field_area(b)) or inside(b["point"], field_area(a)))  # type: ignore[no-untyped-call]
    )


def input_name(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_") or "value"
    return slug if slug[0].isalpha() else f"f_{slug}"


def flag_leaks(log: list[Event], values: set[str]) -> None:
    """Mark (never store) an event whose label, anchor, own text, hint or input name holds one of
    this run's values anywhere inside it ('to account #16785'), so the save refuses it. Numbers
    and words match as redactor does. Run before the values are dropped."""
    redact = redactor(values)
    for ev in log:
        label = ev.get("label") or ev["args"].get("hint")
        texts = (
            ev.get("label"),
            (ev.get("anchor") or {}).get("text"),
            (ev.get("own") or {}).get("text"),
            ev["args"].get("hint"),
            input_name(label) if label else None,  # type: ignore[arg-type]
        )
        if any(redact(t) != t for t in texts if t):  # type: ignore[arg-type]
            ev["leak"] = True
        for key in ("page_texts", "start_texts", "headings", "from_texts"):  # drop, not refuse
            if key in ev:
                ev[key] = [t for t in ev[key] if redact(t) == t]
        if "text_counts" in ev:
            ev["text_counts"] = {t: n for t, n in ev["text_counts"].items() if redact(t) == t}


def without_logout(events: list[Event]) -> list[Event]:
    """C: the agent logs out to leave the site clean. Banking safety (user, 2026-09-29): replay
    must end logged out too, so the trailing run of scrolls and logout clicks becomes ONE logout
    click, last, marked cleanup (it is not the business outcome). A lone logout is the capability.
    """
    end = len(events)
    while end and (
        events[end - 1]["tool"] == "scroll" or norm(events[end - 1].get("text")) in LOGOUT_WORDS
    ):
        end -= 1
    clicks = [ev for ev in events[end:] if ev["tool"] == "click"]
    if not (end and clicks):
        return events
    return [*events[:end], {**clicks[-1], "cleanup": True}]  # type: ignore[typeddict-unknown-key]


def step_events(log: list[Event]) -> list[Event]:
    """R16: drop failures, keep the last success per field. Refuse a take-over."""
    if any(ev.get("recordable") is False for ev in log):
        raise ValueError("a human take-over happened: steps we cannot see. Not saved.")
    ok = [
        ev
        for ev in log
        if ev["tool"] in STEP_TOOLS and not ev["result"].startswith((*FAILED, "BLOCKED", "STOP"))
    ]
    key = lambda ev: (urlparse(ev["url"]).path, ev.get("label") or ev["point"])  # noqa: E731
    last = {key(ev): i for i, ev in enumerate(ok) if ev["tool"] in FIELD_TOOLS}  # type: ignore[no-untyped-call]
    later_select = lambda i: any(  # noqa: E731
        is_select(b) and same_spot(ok[i], b) for b in ok[i + 1 :]
    )
    keep = [
        ev
        for i, ev in enumerate(ok)
        if ev["tool"] not in FIELD_TOOLS
        or (not later_select(i) if is_select(ev) else last[key(ev)] == i)  # type: ignore[no-untyped-call]
    ]
    return without_logout(without_detours(without_no_ops(one_read_per_table(mark_submits(keep)))))


def mark_submits(events: list[Event]) -> list[Event]:
    """A click right after typing into a box on the same page is that form's submit (a login, a
    search), and so is a login click: it changes state, so it is never a detour or a no-op."""
    typed = lambda ev: ev["tool"] in {"type_text", "type_secret"}  # noqa: E731
    page_of = lambda ev: urlparse(ev.get("from_url") or ev["url"]).path  # noqa: E731
    return [
        (
            {**ev, "submit": True}
            if ev["tool"] == "click"
            and (
                ev.get("login")
                or (i and typed(events[i - 1]) and page_of(events[i - 1]) == page_of(ev))  # type: ignore[no-untyped-call]
            )
            else ev
        )
        for i, ev in enumerate(events)
    ]


def one_read_per_table(events: list[Event]) -> list[Event]:
    """A table read again after a scroll is one step: replay scrolls on by itself. The scrolls
    between the reads go too."""
    out: list[Event] = []
    for ev in events:
        name = ev["args"].get("save_as") if ev["tool"] == "extract_table" else None
        first = next(
            (
                i
                for i, o in enumerate(out)
                if o["tool"] == "extract_table" and o["args"]["save_as"] == name
            ),
            None,
        )
        if first is None:
            out.append(ev)
        elif all(o["tool"] == "scroll" for o in out[first + 1 :]):
            del out[first + 1 :]
    return out


def no_op(ev: Event) -> bool:
    """A click that left the site as it was: same page, and it either reloaded that page (a link
    to where you already are) or showed nothing new. A NO CHANGE click never gets here (FAILED)."""
    if ev["tool"] != "click" or "from_url" not in ev or ev.get("landed") or ev.get("submit"):
        return False
    same = urlparse(ev["url"]).path == urlparse(ev["from_url"]).path
    return same and (ev.get("navigated") or not ev.get("new_texts"))


def without_no_ops(events: list[Event]) -> list[Event]:
    """Drop no-op clicks, then keep one of identical clicks in a row (same target on the same
    page, from the same page): a retry, not two steps. A scroll right before a click that loads a
    page (a reload too) is undone by it: dropped."""
    out: list[Event] = []
    for ev in events:
        if ev["tool"] == "click" and (ev.get("navigated") or ev.get("loaded")):
            while out and out[-1]["tool"] == "scroll":
                out.pop()
        if no_op(ev):
            continue
        if out and ev["tool"] == "click" == out[-1]["tool"] and same_click(out[-1], ev):
            out[-1] = ev
        else:
            out.append(ev)
    return out


def same_click(a: Event, b: Event) -> bool:
    here = lambda ev: (  # noqa: E731
        urlparse(ev.get("from_url") or ev["url"]).path,
        ev.get("own"),
        ev.get("label"),
    )
    return bool(a.get("own")) and here(a) == here(b)  # type: ignore[no-untyped-call]


def goes_to_a_page(ev: Event) -> bool:
    """A move between pages. A submit is not a move: it is a step (see mark_submits)."""
    return ev["tool"] == "open_path" or (
        ev["tool"] == "click" and bool(ev.get("loaded")) and not ev.get("submit")
    )


def without_detours(events: list[Event]) -> list[Event]:
    """A run of page changes (navigations, clicks that load a page) with nothing done in between:
    keep only the moves the last one needs. Walking back from the last, an earlier move is kept
    only if the one after it started from a page the move before could not show: its link (a
    click's text) was not on that earlier page. A navigation needs no link, so the ones before it
    are all detours."""
    out: list[Event] = []
    for ev in events:
        if not (goes_to_a_page(ev) and out and goes_to_a_page(out[-1])):
            out.append(ev)
            continue
        run = [ev]
        while out and goes_to_a_page(out[-1]):
            run.insert(0, out.pop())
        out.extend(needed_moves(run))
    return out


def needed_moves(run: list[Event]) -> list[Event]:
    kept = [run[-1]]
    for ev in reversed(run[:-1]):
        nxt = kept[0]
        if nxt["tool"] == "open_path" or norm(nxt.get("text")) in {
            norm(t) for t in ev.get("from_texts", [])
        }:
            continue  # the next move works from the page before ev too
        kept.insert(0, ev)
    return kept

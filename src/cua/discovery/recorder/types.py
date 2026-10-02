"""Typed inputs: an input's type is inferred from the SHAPES of the values typed into it.

A tool logs ``shapes_of(value)`` (a list of type names) next to its event, never the value, so the
recorder can type an input after the run's values are wiped. Pure: no browser, no values kept.

Precedence, when one value matches several shapes ("100" is number, id and integer):
  email, phone, date, currency  -- structural shapes; a value rarely matches one by accident.
  number                        -- before id/integer: an amount typed "100" must still accept
                                   "100.50" at replay; an integer type would refuse it.
  integer                       -- every integer is also a number, so after number it never wins;
                                   listed only so ``shapes_of`` reports every shape that matched.
  id                            -- letters/dashes with a digit ("A12-3"); last, so a plain digit
                                   string (an account, a zip) is a number.
Several values: the shapes ALL of them share, first by precedence; none shared -> "string".
A human's answer during discovery (``human_entry``) is placeholder fake data: people type "1" or
"123" into any box (City, State, Payee). Digits alone cannot tell a text box from a number box, so
a human entry types its input only by a STRUCTURAL shape; number/integer/id from it are dropped.
A wrong "number" makes replay refuse real text; a "string" only skips a check the site still does.
Secrets are never inputs (``{{secret:x}}``), so they are never typed.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import parse_qsl, urlparse

from cua.discovery.recorder.events import input_name
from cua.schema import Event, value_matches_type

PRECEDENCE = ("email", "phone", "date", "currency", "number", "integer", "id")
STRUCTURAL = ("email", "phone", "date", "currency")  # a placeholder rarely matches one by accident


def shapes_of(value: str) -> list[str]:
    """Every shape the whole value matches, in precedence order. Safe to log: names, no value."""
    return [t for t in PRECEDENCE if value.strip() and value_matches_type(value, t)]


def pick_type(shape_lists: Iterable[list[str] | None]) -> str:
    """One input's type from each of its values' shapes. Unknown shapes (None) -> "string"."""
    lists = list(shape_lists)
    if not lists or any(s is None for s in lists):
        return "string"
    common = set.intersection(*(set(s) for s in lists))  # type: ignore[arg-type]
    return next((t for t in PRECEDENCE if t in common), "string")


def event_shapes(ev: Event) -> dict[str, list[str] | None]:
    """input name -> the shapes of the value it took in this event (None: not logged)."""
    if ev["tool"] == "open_path":  # the query values are in the path itself; only shapes leave
        query = urlparse(str(ev["args"]["path"])).query
        return {input_name(k): shapes_of(v) for k, v in parse_qsl(query)}
    if ev["tool"] in {"type_text", "select_option", "request_value"}:
        name = input_name(ev.get("label") or str(ev["args"].get("hint", "")))
        shapes = ev.get("shapes")
        if shapes is None:
            return {name: None}
        keep = STRUCTURAL if ev.get("human_entry") else PRECEDENCE
        return {name: [s for s in shapes if s in keep]}
    return {}


def input_types(events: list[Event]) -> dict[str, str]:
    """input name -> its inferred type, from the events that became steps."""
    seen: dict[str, list[list[str] | None]] = {}
    for ev in events:
        for name, shapes in event_shapes(ev).items():
            seen.setdefault(name, []).append(shapes)
    return {name: pick_type(lists) for name, lists in seen.items()}

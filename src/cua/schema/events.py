"""The discovery event log entry: one tool call, as discovery's ``log()`` writes it.

A type only; nothing uses it yet. The base keys are always present; the rest are extras that some
tools add (``**extra`` in ``log()``) and that the recorder reads back. Labels, points and crops
only: no typed, selected or secret value is ever stored in an event.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic import JsonValue

Point = tuple[int, int] | list[int]


class _EventBase(TypedDict):
    tool: str  # the tool name, or "start" / "send" / "stuck" / "take_over"
    args: dict[str, JsonValue]
    result: str  # first line of the tool's result
    point: Point | None
    url: str
    crop: bytes | str | None  # PNG bytes at log time; a file name once evidence is saved


class Event(_EventBase, total=False):
    """Extras some tools log (rung spots, click outcome, human entry, read targets)."""

    text: str
    own: dict[str, JsonValue] | None  # rung 1: the clicked element's spot
    anchor: dict[str, JsonValue]  # rung 2: the label's spot
    label: str
    offset: list[int]
    index: int | None  # the Nth <select> on the page
    login: bool
    submit: bool  # set by the recorder on a sending click
    from_texts: list[str]
    from_url: str
    loaded: bool
    navigated: bool
    new_texts: bool
    landed: JsonValue
    status: int | None
    path: str
    dropdown: bool
    field_box: JsonValue
    human_entry: bool
    recordable: bool
    url_before: str
    seconds: int
    actions: list[JsonValue]
    shot_before: bytes | str | None
    shot_after: bytes | str | None
    corrected: list[str]
    table: JsonValue  # an extract's table cell
    page_texts: list[str]
    headings: list[str]
    pattern: str | None
    continued: bool
    header: JsonValue
    columns_x: list[list[int]]
    leak: bool
    text_counts: dict[str, int]
    start_texts: list[str]

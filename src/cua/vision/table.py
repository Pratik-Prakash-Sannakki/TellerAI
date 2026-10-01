"""The shared OCR table reader: discovery and replay use it to find a table's columns from a
header and read the rows under it (byte-identical in both notebooks: discovery.py 1346-1455,
replay.py 1115-1224, apart from comments; pinned by tests/replay/test_table_replay.py).

Moved verbatim (bodies unchanged): ``same_line``, ``column_spans``, ``table_columns``, ``col_of``,
``text_lines``, ``row_of``, ``read_rows``, ``like_rows``, ``cell_shape``, ``append_rows``. None of
these read a module global other than ``TABLE_GAP`` itself (a constant, not run state).

``KEY_REACH`` and ``is_word`` (discovery.py 1347, 1457) are discovery-only -- table_cell/
column_header, which use them, are not part of this shared reader and are out of this step's
scope (they stay with discovery's own port).
"""

from __future__ import annotations

import re
from collections.abc import Callable

from cua.vision.look import Box, Element, Look

TABLE_GAP = 40  # px: a bigger vertical gap between two lines ends a table block


def same_line(a: Box, b: Box) -> bool:
    return a.y1 < b.y2 and b.y1 < a.y2


def column_spans(line: list[Element]) -> list[tuple[Element, float, float]]:
    """Each header's x-range: out to the midpoint with its neighbours on the header line; an
    outer header reaches one own width further (a cell may be wider than its header)."""
    line = sorted(line, key=lambda e: e.box.x1)
    out = []
    for i, e in enumerate(line):
        w = e.box.x2 - e.box.x1
        lo = (line[i - 1].box.x2 + e.box.x1) / 2 if i else e.box.x1 - w
        hi = (e.box.x2 + line[i + 1].box.x1) / 2 if i + 1 < len(line) else e.box.x2 + w
        out.append((e, lo, hi))
    return out


def table_columns(
    look: Look, head: Element, columns: list[str], match: Callable[[str, str], bool]
) -> tuple[list[tuple[str | None, float, float]], int] | None:
    """(every header-line column as (asked name or None, lo, hi), the header line's bottom), or
    None when an asked column is not on head's line. Unasked columns stay: they bound the others."""
    spans = column_spans([e for e in look.elements if same_line(e.box, head.box)])
    names = {id(e): next((c for c in columns if match(e.text, c)), None) for e, _, _ in spans}
    if set(columns) - set(names.values()):
        return None
    below = max(e.box.y2 for e, _, _ in spans)
    return [(names[id(e)], lo, hi) for e, lo, hi in spans], below


def col_of(box: Box, cols: list[tuple[str | None, float, float]]) -> int | None:
    """The column the box overlaps most, or None when it overlaps none (outside the table)."""
    lap = [min(box.x2, hi) - max(box.x1, lo) for _, lo, hi in cols]
    best = max(range(len(cols)), key=lap.__getitem__, default=None)
    return best if best is not None and lap[best] > 0 else None


def text_lines(els: list[Element]) -> list[list[Element]]:
    """Texts grouped into lines, top to bottom."""
    lines: list[list[Element]] = []
    for e in sorted(els, key=lambda e: e.box.y1):
        if lines and same_line(lines[-1][0].box, e.box):
            lines[-1].append(e)
        else:
            lines.append([e])
    return lines


def row_of(line: list[Element], cols: list[tuple[str | None, float, float]]) -> dict[str, str]:
    """A line's texts in the asked columns, left to right; two texts in one column are joined."""
    row: dict[str, str] = {}
    for e in sorted(line, key=lambda e: e.box.x1):
        if (name := cols[col_of(e.box, cols)][0]) is not None:  # type: ignore[index]
            row[name] = f"{row[name]} {e.text}" if name in row else e.text
    return row


def read_rows(
    look: Look, cols: list[tuple[str | None, float, float]], below: int | None, limit: int
) -> tuple[list[dict[str, str]], bool]:
    """(rows under the header, whether the table may continue past the look's bottom). Rows end at
    a vertical gap >= TABLE_GAP, a line with no text in any asked column, or `limit`. below=None:
    a scrolled table with its header gone, read from the look's top."""
    inside = [
        e
        for e in look.elements
        if col_of(e.box, cols) is not None and (below is None or e.box.y1 >= below)
    ]
    rows: list[dict[str, str]] = []
    prev, height = below, None
    for line in text_lines(inside):
        row = row_of(line, cols)
        top = min(e.box.y1 for e in line)
        gap = prev is not None and top - prev >= max(TABLE_GAP, 2 * (height or 0))
        if gap or not row or len(rows) >= limit or not like_rows(row, rows):
            return rows, False
        rows.append(row)
        height = height or max(e.box.y2 for e in line) - top
        prev = max(e.box.y2 for e in line)
    return rows, len(rows) < limit


def like_rows(row: dict[str, str], rows: list[dict[str, str]]) -> bool:
    """A table's end: a line that no longer looks like its rows (a footer, a menu, a copyright). Each
    column's cells keep one shape (a date stays a date, an amount an amount); a line breaking the
    shape of a column the rows so far all agree on is not a row. Links joined by '|' never are."""
    if any("|" in v or len(v) > 60 for v in row.values()):
        return False
    for name, v in row.items():
        seen = {cell_shape(r[name]) for r in rows if name in r}
        if len(seen) == 1 and cell_shape(v) not in seen:
            return False
    return True


def cell_shape(text: str) -> str:
    """'date', 'amount', or 'text': enough to tell a row cell from a footer line in its column."""
    t = text.strip()
    if re.fullmatch(r"\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}", t):
        return "date"
    if re.fullmatch(r"[-−]?\$?[-−]?[\d,]+(\.\d{2})?", t):
        return "amount"
    return "text"


def append_rows(old: list[dict[str, str]], new: list[dict[str, str]]) -> list[dict[str, str]]:
    """A scrolled second read repeats the rows still on screen: drop only that overlap."""
    k = next((k for k in range(min(len(old), len(new)), 0, -1) if old[-k:] == new[:k]), 0)
    return [*old, *new[k:]]

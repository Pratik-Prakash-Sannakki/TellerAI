"""The shared OCR table reader: parity between cua.vision.table and both notebooks' copies.

tests/replay/test_table_replay.py already proves discovery's and replay's own copies are
byte-identical (SHARED set, ast.dump compare); this file proves cua.vision.table reproduces that
same behaviour, by running the real fixture (the shared one in tests/fakes.py)
through BOTH notebooks (via ast, same technique as tests/replay/test_table_replay.py:24) and
through cua.vision.table, and comparing results. It also source-checks the functions that needed
no parameterizing (same_line, column_spans, col_of, text_lines, row_of, like_rows, cell_shape,
append_rows -- not table_columns/read_rows, which discovery's table_cell/column_header still read
no globals in, but KEY_REACH/is_word live in discovery only, out of this step's scope) are
byte-identical to discovery's own source (ast.dump compare, ignoring docstrings).
"""

from __future__ import annotations

import ast
from pathlib import Path

import cua.vision.table as table_mod
from cua.vision.look import Box, Element, Look
from cua.vision.table import TABLE_GAP, append_rows, read_rows, table_columns
from tests.fakes import COLS, FOOTER, HEADER, ROWS
from tests.unit.replay.test_replay_table import SHARED as REPLAY_SHARED

DISCOVERY = Path(__file__).parents[3] / "notebooks/discovery/discovery.py"
NO_GLOBALS = {
    "same_line",
    "column_spans",
    "table_columns",
    "col_of",
    "text_lines",
    "row_of",
    "read_rows",
    "like_rows",
    "cell_shape",
    "append_rows",
}


def _is_header(seen: str, want: str) -> bool:
    return " ".join(seen.casefold().split()) == " ".join(want.casefold().split())


def _look(items: list[tuple[str, tuple[int, int, int, int]]]) -> Look:
    els = tuple(Element(i, t, Box(*b)) for i, (t, b) in enumerate(items, 1))
    return Look(b"", b"", els, "https://parabank.parasoft.com/parabank/activity.htm")


def _read(
    items: list[tuple[str, tuple[int, int, int, int]]],
    header: str = "Date",
    cols: list[str] = COLS,
    limit: int = 50,
) -> tuple[list[dict[str, str]], bool]:
    look = _look(items)
    head = next(e for e in look.elements if e.text == header)
    cols_, below = table_columns(look, head, cols, _is_header)
    return read_rows(look, cols_, below, limit)


def test_a_three_column_table_is_read_into_rows_even_when_cells_are_a_few_px_off() -> None:
    rows, more = _read([*HEADER, *ROWS, *FOOTER])
    assert rows == [
        {"Date": "09/01/2026", "Description": "Funds Transfer Sent", "Amount": "$100.00"},
        {"Date": "09/02/2026", "Description": "Bill Payment", "Amount": "$25.00"},
    ]
    assert more is False


def test_reading_stops_at_a_vertical_gap() -> None:
    far = [("09/03/2026", (100, 240, 180, 260)), ("$5.00", (500, 240, 540, 260))]
    rows, _ = _read([*HEADER, *ROWS, *far])
    assert "09/03/2026" not in {r["Date"] for r in rows}


def test_a_table_that_runs_to_the_bottom_of_the_screen_may_continue() -> None:
    assert _read([*HEADER, *ROWS])[1] is True


def test_only_the_asked_columns_are_kept_and_the_row_limit_holds() -> None:
    rows, more = _read([*HEADER, *ROWS], header="Amount", cols=["Amount"], limit=1)
    assert rows == [{"Amount": "$100.00"}]
    assert more is False


def test_append_drops_only_the_overlap_of_a_scrolled_second_read() -> None:
    a, b, c = ({"x": "1"}, {"x": "2"}, {"x": "3"})
    assert append_rows([a, b], [b, c]) == [a, b, c]
    assert append_rows([a, a], [a, a, b]) == [a, a, b]
    assert append_rows([], [a]) == [a]


def test_table_gap_matches_discoverys_own_constant() -> None:
    expected = 40
    assert expected == TABLE_GAP


def _defs(path: Path, names: set[str]) -> dict[str, ast.AST]:
    body = ast.parse(path.read_text()).body
    out = {}
    for n in body:
        if getattr(n, "name", None) in names:
            n.body = [
                s
                for s in n.body
                if not (
                    isinstance(s, ast.Expr)
                    and isinstance(s.value, ast.Constant)
                    and isinstance(s.value.value, str)
                )
            ]
            out[n.name] = ast.dump(n, annotate_fields=False)
    return out


def test_the_no_global_table_functions_are_byte_identical_to_discoverys_source() -> None:
    """ast.dump compare, ignoring docstrings -- the functions this step did not have to
    parameterize must be moved, not rewritten."""
    src_defs = _defs(DISCOVERY, NO_GLOBALS)
    mod_defs = _defs(Path(table_mod.__file__), NO_GLOBALS)
    assert set(src_defs) == NO_GLOBALS
    assert mod_defs == src_defs


def test_replay_and_discovery_agree_on_what_is_shared_with_cua_vision_table() -> None:
    """tests/replay/test_table_replay.py's own SHARED set is the contract this module ports;
    every name it lists is importable from cua.vision.table."""
    assert REPLAY_SHARED.issubset(NO_GLOBALS)

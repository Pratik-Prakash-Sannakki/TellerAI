"""do_extract_table: find the header by its label, read the rows with discovery's own reader.
Ported from tests/replay/test_table_replay.py (its evidence tests are in test_evidence.py)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cua.replay import engine, steps
from cua.replay.context import Ctx
from cua.schema import Capability, ReplayResult
from cua.vision import Look
from tests.unit._snapshots import DISCOVERY as SNAP_DISCOVERY
from tests.unit._snapshots import REPLAY as SNAP_REPLAY
from tests.unit.replay.helpers import cap, make_replay_ctx, mk_look

ROOT = Path(__file__).parents[3]
DISCOVERY = SNAP_DISCOVERY
REPLAY = SNAP_REPLAY
SHARED = {
    "col_of",
    "same_line",
    "table_columns",
    "column_spans",
    "text_lines",
    "row_of",
    "read_rows",
    "append_rows",
    "like_rows",
    "cell_shape",
}
# Same fixture as tests/discovery/test_extract_table.py (copied: that file is another step's).
COLS = ["Date", "Description", "Amount"]
HEADER = [
    ("Date", (100, 100, 140, 120)),
    ("Description", (250, 100, 350, 120)),
    ("Amount", (500, 100, 560, 120)),
    ("Account Services", (0, 100, 80, 120)),
]
ROWS = [
    ("09/01/2026", (96, 130, 180, 150)),
    ("Funds Transfer Sent", (255, 130, 400, 150)),
    ("$100.00", (507, 130, 560, 150)),
    ("09/02/2026", (104, 160, 188, 180)),
    ("Bill Payment", (245, 160, 340, 180)),
    ("$25.00", (495, 160, 545, 180)),
]
FOOTER = [("About Us", (100, 260, 170, 280))]  # 80px below the last row: not in the table
WANT = [
    {"Date": "09/01/2026", "Description": "Funds Transfer Sent", "Amount": "$100.00"},
    {"Date": "09/02/2026", "Description": "Bill Payment", "Amount": "$25.00"},
]


def _defs(path: Path) -> dict[str, object]:
    body = ast.parse(path.read_text()).body
    out: dict[str, object] = {n.name: ast.unparse(n) for n in body if getattr(n, "name", None) in SHARED}  # type: ignore[attr-defined]
    gap = next(
        n
        for n in body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TABLE_GAP"
    )
    return {**out, "TABLE_GAP": ast.literal_eval(gap.value)}


def test_the_table_reader_is_identical_to_discoverys() -> None:
    assert _defs(REPLAY) == _defs(DISCOVERY) and set(_defs(REPLAY)) == SHARED | {"TABLE_GAP"}


def _cap(**step: object) -> Capability:
    s = {
        "action": "extract_table",
        "header": {"label": "Date"},
        "columns": COLS,
        "save_as": "transactions_1",
        **step,
    }
    return cap(
        [s],
        "Account Activity",
        outputs=[
            {"name": "transactions_1", "type": "table", "description": "rows", "columns": COLS}
        ],
    )


class Mouse:
    async def wheel(self, *a: float) -> None:
        return None


class Page:
    mouse = Mouse()


async def _run(
    looks: list[list[tuple[str, tuple[int, int, int, int]]]], mp: pytest.MonkeyPatch, **step: object
) -> tuple[Ctx, bool]:
    """Each scroll shows the next look."""
    queue = list(looks)
    ctx = make_replay_ctx(Page(), look=mk_look(queue.pop(0)))

    async def act(c: Ctx, *s: object) -> Look:
        c.run.look = mk_look(queue.pop(0)) if queue else c.run.look
        return c.run.look  # type: ignore[return-value]

    mp.setattr(steps, "act", act)
    cp = _cap(**step)
    return ctx, await steps.do_extract_table(ctx, cp.steps[0], None, cp)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_replay_reads_the_fixture_into_the_same_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, ok = await _run([[*HEADER, *ROWS, *FOOTER]], monkeypatch)
    assert ok is True and ctx.run.outputs["transactions_1"] == WANT


@pytest.mark.asyncio
async def test_an_empty_table_is_a_valid_output(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, ok = await _run([[*HEADER, *FOOTER]], monkeypatch)
    assert ok is True and ctx.run.outputs["transactions_1"] == []


@pytest.mark.asyncio
async def test_a_missing_header_is_a_failed_check(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, ok = await _run([FOOTER], monkeypatch)
    assert ok is False and "transactions_1" not in ctx.run.outputs


@pytest.mark.asyncio
async def test_a_table_past_the_screen_is_read_on_after_a_scroll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    more = [
        ("09/02/2026", (104, 10, 188, 30)),
        ("Bill Payment", (245, 10, 340, 30)),
        ("$25.00", (495, 10, 545, 30)),
        ("09/03/2026", (100, 40, 180, 60)),
        ("ATM", (250, 40, 290, 60)),
        ("$5.00", (500, 40, 540, 60)),
        *FOOTER,
    ]
    ctx, ok = await _run([[*HEADER, *ROWS], more], monkeypatch)
    assert ok is True
    assert [r["Description"] for r in ctx.run.outputs["transactions_1"]] == [  # type: ignore[index]
        "Funds Transfer Sent",
        "Bill Payment",
        "ATM",
    ]


@pytest.mark.asyncio
async def test_the_row_limit_holds(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, ok = await _run([[*HEADER, *ROWS]], monkeypatch, row_limit=1)
    assert ok is True and ctx.run.outputs["transactions_1"] == WANT[:1]


def test_a_table_step_needs_no_target() -> None:
    cp = _cap()
    assert getattr(cp.steps[0], "target", None) is None and "extract_table" in steps.ACTIONS
    assert engine.read_only_done(make_replay_ctx(), cp, []) is True


def test_the_outputs_line_shows_rows() -> None:
    assert "Bill Payment" in ReplayResult("SUCCESS", {"transactions_1": WANT}, []).outputs_line  # type: ignore[dict-item]


# Accounts Overview as live OCR sees it (discovery run 20261003T004411Z: header box
# [484, 318, 550, 342], columns_x [452.5, 575] [575, 700.5] [700.5, 974]). The left menu's
# "Account Services" and the title "Accounts Overview" start with "Account" and sit above the
# header; the menu's own "Accounts Overview" shares the header's line and reaches below its bottom,
# and "Transfer Funds" sits beside the data row. A "Total" line and a footnote end the table.
OVERVIEW = [
    ("Account Services", (297, 270, 420, 290)),
    ("Accounts Overview", (484, 270, 640, 295)),
    ("Open New Account", (297, 300, 420, 320)),
    ("Account", (484, 318, 550, 342)),
    ("Balance*", (600, 318, 689, 342)),
    ("Available Amount", (712, 318, 843, 342)),
    ("Accounts Overview", (297, 324, 421, 346)),
    ("13344", (484, 345, 530, 365)),
    ("$5022.93", (600, 345, 668, 365)),
    ("$5022.93", (712, 345, 780, 365)),
    ("Transfer Funds", (297, 349, 400, 369)),
    ("Bill Pay.", (297, 374, 355, 394)),
    ("Total $5022.93", (484, 378, 668, 398)),
    ("Find Transactions", (297, 399, 420, 419)),
    ("*Balance includes deposits that may be subject to holds", (484, 402, 860, 420)),
    ("Update Contact Info", (297, 424, 430, 444)),
]


@pytest.mark.asyncio
async def test_the_header_skips_menu_items_that_only_start_with_its_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cols = ["Account", "Balance*", "Available Amount"]
    ctx, ok = await _run(
        [OVERVIEW], monkeypatch, header={"label": "Account", "ordinal": 1}, columns=cols
    )
    assert ok is True
    assert ctx.run.outputs["transactions_1"] == [
        {"Account": "13344", "Balance*": "$5022.93", "Available Amount": "$5022.93"}
    ]


@pytest.mark.asyncio
async def test_label_hits_without_the_columns_are_a_failed_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    menu_only = OVERVIEW[:2]
    ctx, ok = await _run(
        [menu_only], monkeypatch, header={"label": "Account"}, columns=["Account", "Balance*"]
    )
    assert ok is False and "transactions_1" not in ctx.run.outputs


@pytest.mark.asyncio
async def test_menu_items_at_the_header_and_row_heights_do_not_hide_the_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Live ParaBank: "Accounts Overview" (menu) reaches below the header into the first row, and
    # "Transfer Funds" (menu) sits on a line of its own between the row and the Total line.
    beside = [
        ("Account", (200, 100, 260, 120)),
        ("Balance*", (350, 100, 420, 120)),
        ("Available Amount", (500, 100, 620, 120)),
        ("Accounts Overview", (0, 110, 130, 135)),
        ("13344", (200, 130, 250, 150)),
        ("$5022.93", (350, 130, 420, 150)),
        ("$5022.93", (510, 130, 580, 150)),
        ("Transfer Funds", (0, 138, 110, 160)),
        ("Total $5022.93", (330, 160, 430, 180)),
    ]
    cols = ["Account", "Balance*", "Available Amount"]
    ctx, ok = await _run([beside], monkeypatch, header={"label": "Account"}, columns=cols)
    assert ok is True
    assert ctx.run.outputs["transactions_1"] == [
        {"Account": "13344", "Balance*": "$5022.93", "Available Amount": "$5022.93"}
    ]

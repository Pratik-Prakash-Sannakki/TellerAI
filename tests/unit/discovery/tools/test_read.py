"""extract_value / extract_table: the agent points at a box or a header, our code reads it; the log
holds labels and positions only, never a value.

Ported from tests/discovery/test_extract_table.py (the tool and the footer/shape/empty-cell
reader cases), test_wandering.py (value_in_box) and test_read_runs.py (read_target/table_cell).
"""

from __future__ import annotations

import re

import pytest

from cua.browser.dropdown import SELECT_UNDER_POINT_JS
from cua.discovery.context import Ctx
from cua.discovery.tools import read
from cua.discovery.tools.read_helpers import (
    Spot,
    is_header,
    read_target,
    table_cell,
    value_in_box,
)
from cua.vision.look import Box, Look
from cua.vision.table import read_rows, table_columns
from tests.fakes import (
    COLS,
    FOOTER,
    HEADER,
    ROWS,
    ActTab,
    blank_png,
    make_ctx,
    make_look,
    make_session,
)

Items = list[tuple[str, tuple[int, int, int, int]]]
ACTIVITY = "https://example.test/app/activity.htm"
TRANSFER = "https://example.test/app/transfer.htm"


@pytest.fixture(autouse=True)
def _no_crop_pixels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(read, "crop", lambda *a: b"crop")


def _tool(name: str, ctx: Ctx):  # type: ignore[no-untyped-def]
    return {t.name: t for t in read.make_read_tools(ctx)}[name]


async def _table(ctx: Ctx, items: Items, **kw: object) -> str:
    ctx.run.look = make_look(items)
    args = {"header_ref": 1, "save_as": "transactions_1", "columns": COLS, "description": "rows"}
    return await _tool("extract_table", ctx).ainvoke({**args, **kw})  # type: ignore[no-any-return]


# --- extract_table ---


@pytest.mark.asyncio
async def test_the_tool_saves_rows_and_logs_labels_only() -> None:
    ctx = make_ctx()
    msg = await _table(ctx, [*HEADER, *ROWS, *FOOTER])
    assert ctx.run.saved["transactions_1"][1]["Description"] == "Bill Payment"  # type: ignore[index]
    assert msg.startswith("Saved 2 rows")
    assert "continue below" not in msg
    ev = ctx.run.log[-1]
    assert ev["tool"] == "extract_table"
    assert ev["label"] == "Date"
    assert ev["args"]["columns"] == COLS
    assert ev["header"]["ordinal"] == 1  # type: ignore[index]
    assert ev["args"]["row_limit"] == 50  # noqa: PLR2004
    assert ev["continued"] is False
    blob = str(ev)
    for v in ("09/01/2026", "Funds Transfer", "$100.00", "Bill Payment", "$25.00"):
        assert v not in blob


@pytest.mark.asyncio
async def test_a_second_call_with_the_same_name_appends_after_a_scroll() -> None:
    ctx = make_ctx()
    assert "continue below" in await _table(ctx, [*HEADER, *ROWS])
    scrolled = [
        ("09/02/2026", (104, 10, 188, 30)),
        ("Bill Payment", (245, 10, 340, 30)),
        ("$25.00", (495, 10, 545, 30)),
        ("09/03/2026", (100, 40, 180, 60)),
        ("ATM", (250, 40, 290, 60)),
        ("$5.00", (500, 40, 540, 60)),
    ]
    msg = await _table(ctx, scrolled)  # header gone: the saved columns are used
    assert msg.startswith("Saved 1 rows")
    assert "3 in all" in msg
    rows = ctx.run.saved["transactions_1"]
    assert [r["Description"] for r in rows] == ["Funds Transfer Sent", "Bill Payment", "ATM"]  # type: ignore[index]
    assert ctx.run.log[-1]["continued"] is True


@pytest.mark.asyncio
async def test_a_header_holding_a_run_value_is_refused() -> None:
    ctx = make_ctx()
    ctx.run.redact = {"13566"}
    items = [("Account 13566", (100, 100, 200, 120)), ("Amount", (500, 100, 560, 120))]
    msg = await _table(ctx, items, columns=["Account 13566", "Amount"])
    assert msg.startswith("REFUSED")
    assert not ctx.run.log


@pytest.mark.asyncio
async def test_columns_not_on_the_header_row_are_refused() -> None:
    msg = await _table(make_ctx(), [*HEADER, *ROWS], columns=["Date", "Balance"])
    assert msg.startswith("REFUSED")


@pytest.mark.asyncio
async def test_a_stale_header_ref_says_observe() -> None:
    assert (await _table(make_ctx(), [*HEADER], header_ref=99)).startswith("STALE")


def _read(items: Items, header: str = "Date") -> tuple[list[dict[str, str]], bool]:
    look = make_look(items)
    head = next(e for e in look.elements if e.text == header)
    found = table_columns(look, head, COLS, is_header)
    assert found is not None
    return read_rows(look, found[0], found[1], 50)


def test_the_footer_and_menu_links_below_the_table_are_never_rows() -> None:
    """Live run: the page footer sat less than TABLE_GAP under the last row and was read as two
    more transactions."""
    footer = [
        ("Home | About Us I Services | Products I Locations", (240, 190, 480, 208)),
        ("Contact Us", (500, 190, 560, 208)),
        ("© Parasoft. All rights reserved. Visit us at:www.parasoft.com", (96, 214, 400, 232)),
    ]
    rows, more = _read([*HEADER, *ROWS, *footer])
    assert [r["Date"] for r in rows] == ["09/01/2026", "09/02/2026"]
    assert more is False


def test_a_line_that_breaks_a_columns_shape_ends_the_table() -> None:
    odd = [("Total", (100, 190, 140, 208)), ("$125.00", (500, 190, 560, 208))]  # not a date
    rows, _ = _read([*HEADER, *ROWS, *odd])
    assert len(rows) == 2  # noqa: PLR2004


def test_rows_with_an_empty_cell_are_still_rows() -> None:
    more = [("09/03/2026", (100, 190, 180, 208)), ("Funds Transfer Received", (250, 190, 420, 208))]
    rows, _ = _read([*HEADER, *ROWS, *more])
    assert len(rows) == 3  # noqa: PLR2004
    assert "Amount" not in rows[2]


# --- extract_value ---


@pytest.mark.asyncio
async def test_extract_value_echoes_an_id_by_its_last_digits_only() -> None:
    """The model's echo of a saved account id showed the full number; the saved value stays
    whole (it is the run's output, in memory)."""
    ctx = make_ctx()
    ctx.run.look = make_look([("Account", (10, 60, 90, 80)), ("98765", (150, 60, 220, 80))])
    args = {"ref": 2, "save_as": "acct", "value_type": "string", "description": "account"}
    assert await _tool("extract_value", ctx).ainvoke(args) == "Saved acct = '***765'."
    assert ctx.run.saved == {"acct": "98765"}


@pytest.mark.asyncio
async def test_extract_value_saves_the_value_and_logs_only_where_it_is() -> None:
    ctx = make_ctx()
    ctx.run.look = make_look(
        [
            ("Customer Care", (10, 60, 140, 80)),
            ("www.x.com or call 888-305-0041", (150, 60, 400, 80)),
        ]
    )
    args = {"ref": 2, "save_as": "phone", "value_type": "phone", "description": "phone"}
    assert await _tool("extract_value", ctx).ainvoke(args) == "Saved phone = '888-305-0041'."
    assert ctx.run.saved == {"phone": "888-305-0041"}
    ev = ctx.run.log[-1]
    assert ev["label"] == "Customer Care"
    assert ev["pattern"] is not None
    assert ev["table"] is None
    assert ev["crop"] == b"crop"
    assert ev["page_texts"] == ["Customer Care"]


@pytest.mark.asyncio
async def test_extract_value_refuses_a_box_without_the_type_and_a_stale_ref() -> None:
    ctx = make_ctx()
    ctx.run.look = make_look([("Balance", (10, 60, 140, 80))])
    tool = _tool("extract_value", ctx)
    base = {"save_as": "b", "value_type": "currency", "description": "b"}
    assert (await tool.ainvoke({"ref": 1, **base})).startswith("REFUSED")
    assert (await tool.ainvoke({"ref": 7, **base})).startswith("STALE")
    assert not ctx.run.saved


@pytest.mark.parametrize(
    ("box", "kind", "value", "has_pattern"),
    [
        ("www.parasoft.com or call 888-305-0041", "phone", "888-305-0041", True),
        ("888-305-0041", "phone", "888-305-0041", False),
        ("Balance: -$202,484.50 today", "currency", "-$202,484.50", True),
        ("-$202484.50", "currency", "-$202484.50", False),
        ("Write to info@parabank.example now", "email", "info@parabank.example", True),
        ("Opened 09/30/2026", "date", "09/30/2026", True),
    ],
)
def test_the_value_is_the_first_match_of_its_shape_inside_the_box(
    box: str, kind: str, value: str, has_pattern: bool
) -> None:
    found = value_in_box(box, kind)
    assert found is not None
    got, pattern = found
    assert got == value
    assert (pattern is not None) is has_pattern
    if pattern:
        assert re.search(pattern, box).group() == value  # type: ignore[union-attr]
        assert value not in pattern


def test_a_box_without_the_shape_is_refused() -> None:
    assert value_in_box("Call us any time", "phone") is None


def test_a_whole_box_type_takes_the_whole_box() -> None:
    assert value_in_box("Savings", "string") == ("Savings", None)
    assert value_in_box("yes", "boolean") == ("yes", None)
    assert value_in_box("", "string") is None


# --- read_target / table_cell (ParaBank's Accounts Overview, shaped from a live run) ---

OVERVIEW = [
    ("Account Services", (20, 200, 170, 218)),
    ("Accounts Overview", (330, 200, 500, 222)),
    ("Open New Account", (20, 236, 150, 252)),
    ("Account", (330, 236, 390, 252)),
    ("Balance*", (560, 236, 625, 252)),
    ("Available Amount", (800, 236, 930, 252)),
    ("Transfer Funds", (20, 262, 130, 278)),
    ("13566", (330, 262, 380, 278)),
    ("-$202484.50", (560, 262, 660, 278)),
    ("$0.00", (800, 262, 845, 278)),
    ("Bill Pay", (20, 288, 80, 304)),
    ("Total", (330, 288, 370, 304)),
    ("-$202484.50", (560, 288, 660, 304)),
]
BALANCE = 8  # the first data row's balance
GRID = [
    ("Account Services", (20, 170, 160, 190)),
    ("Account Types", (400, 170, 540, 192)),
    ("Open New Account", (20, 200, 150, 216)),
    ("Type", (400, 200, 440, 216)),
    ("Balance", (600, 200, 660, 216)),
    ("Transfer Funds", (20, 226, 130, 242)),
    ("Checking", (400, 226, 470, 242)),
    ("$100.00", (600, 226, 670, 242)),
    ("Bill Pay", (20, 252, 80, 268)),
    ("Savings", (400, 252, 465, 268)),
    ("$25.00", (600, 252, 655, 268)),
]


def _cell(*texts: tuple[str, tuple[int, int, int, int]], value: str) -> dict[str, str] | None:
    look = make_look(list(texts), ACTIVITY)
    return table_cell(look, next(e for e in look.elements if e.text == value), set())


def test_the_first_accounts_balance_never_uses_the_menu_or_the_title() -> None:
    """Live: row_key 'Transfer Funds' (menu), column 'Accounts Overview' (title); replay read
    13566."""
    look: Look = make_look(OVERVIEW, ACTIVITY)
    balance = look.elements[BALANCE]
    got: Spot = read_target(look, balance, set())
    assert got["table"] is None  # the row key would be an account number: a value
    assert got["label"] == "Balance*"
    anchor = got["anchor"]
    assert anchor["text"] == "Balance*"  # type: ignore[index]
    assert anchor["ordinal"] == 1  # type: ignore[index]
    for chrome in ("Transfer Funds", "Accounts Overview", "Account Services"):
        assert chrome not in str(got)
    hx, hy = Box(*anchor["box"]).center  # type: ignore[index]  # replay's rung 2: header + offset
    dx, dy = got["offset"]  # type: ignore[misc]
    assert balance.box.contains(hx + dx, hy + dy)


def test_a_nav_link_and_a_banner_are_not_a_table() -> None:
    """Live: available_amount got row_key 'Transfer Funds', column 'Welcome to Account Services'."""
    assert (
        _cell(
            ("Welcome to Account Services", (400, 100, 700, 120)),
            ("Transfer Funds", (20, 300, 130, 320)),
            ("Available:", (300, 300, 380, 320)),
            ("$515.50", (420, 300, 490, 320)),
            value="$515.50",
        )
        is None
    )


def test_a_menu_as_far_from_the_grid_as_its_columns_are_is_unsure() -> None:
    """Menu gap == column gap: nothing tells them apart, so no row key (the anchor is used)."""
    assert _cell(*OVERVIEW, value="$0.00") is None


def test_a_real_grid_gives_its_own_row_key_and_nearest_header() -> None:
    assert _cell(*GRID, value="$25.00") == {"row_key": "Savings", "column": "Balance"}
    assert _cell(*GRID, value="$100.00") == {"row_key": "Checking", "column": "Balance"}


def test_a_row_key_that_is_a_number_or_a_run_value_is_no_key() -> None:
    grid = [*GRID[:9], ("14454", (400, 252, 450, 268)), GRID[10]]
    assert _cell(*grid, value="$25.00") is None
    look = make_look(GRID, ACTIVITY)
    assert table_cell(look, look.elements[10], {"savings"}) is None


def test_a_header_far_above_the_value_is_not_its_column() -> None:
    texts = [
        ("Type", (300, 100, 340, 120)),
        ("Amount", (420, 100, 490, 120)),
        ("Checking", (300, 300, 390, 320)),
        ("$25.00", (420, 300, 490, 320)),
    ]
    assert _cell(*texts, value="$25.00") is None


def test_a_two_column_table_with_no_menu_keeps_its_row_key() -> None:
    texts = [
        ("Type", (100, 100, 140, 116)),
        ("Balance", (300, 100, 360, 116)),
        ("Savings", (100, 126, 165, 142)),
        ("$25.00", (300, 126, 355, 142)),
    ]
    assert _cell(*texts, value="$25.00") == {"row_key": "Savings", "column": "Balance"}


# --- extract_options ---

TRANSFER_FORM = [
    ("From account #:", (480, 345, 590, 365)),
    ("Transfer Funds", (300, 100, 500, 130)),
]
ACCOUNTS = ["***010", "14232", "15120"]


def _options_ctx(options: list[str] | None, index: int | None = 0) -> Ctx:
    """A transfer page whose dropdown at (720, 355) lists ``options`` (None: no dropdown there)."""
    page = ActTab(TRANSFER)

    def answer(script: str, arg: object) -> object:
        if script == SELECT_UNDER_POINT_JS:
            return index if options is not None else None
        return options

    page.answer = answer  # type: ignore[method-assign]
    ctx = make_ctx(make_session(page))
    ctx.run.look = make_look(TRANSFER_FORM, url=TRANSFER, png=blank_png())
    return ctx


async def _extract_options(ctx: Ctx) -> str:
    args = {"x": 720, "y": 355, "save_as": "from_accounts", "description": "From accounts"}
    return await _tool("extract_options", ctx).ainvoke(args)  # type: ignore[no-any-return]


@pytest.mark.asyncio
async def test_extract_options_saves_the_list_and_logs_no_option() -> None:
    ctx = _options_ctx(ACCOUNTS)
    msg = await _extract_options(ctx)
    assert msg.startswith("Saved 3 options to from_accounts.")
    assert ctx.run.saved["from_accounts"] == ACCOUNTS
    ev = ctx.run.log[-1]
    assert ev["tool"] == "extract_options"
    assert ev["label"] == "From account #:"
    assert ev["anchor"]["text"] == "From account #:"  # type: ignore[index]
    assert ev["index"] == 0
    assert ev["point"] == (720, 355)
    assert ev["args"] == {
        "ref": None,
        "x": 720,
        "y": 355,
        "save_as": "from_accounts",
        "description": "From accounts",
    }
    for v in ACCOUNTS:
        assert v not in str(ev)
        assert v not in msg


@pytest.mark.asyncio
async def test_extract_options_off_a_dropdown_is_refused() -> None:
    ctx = _options_ctx(None)
    msg = await _extract_options(ctx)
    assert msg.startswith("REFUSED: no dropdown at (720, 355)")
    assert "from_accounts" not in ctx.run.saved

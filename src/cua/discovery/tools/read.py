"""The tools that read values off the page: extract_value, extract_table and extract_options.

Moved from discovery.py 1567-1592 (extract_value) and 1612-1650 (extract_table). Each tool keeps
its checks; the rest is ``_saved_value`` / ``_columns`` + ``_saved_rows`` + ``_log_table``, bodies
otherwise unchanged. The pure helpers they use
(value_in_box, read_target, is_header, off_table, ...) are in ``read_helpers``; the shared table
reader is ``cua.vision.table``. Tool names, signatures and docstrings are the notebook's.
``extract_options`` (new, 2026-10-02) reads a native dropdown's options through the dropdown
exception (``list_options``): its list never shows in a screenshot, so it cannot be read by OCR.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from cua.discovery.context import Ctx, crop, dropdown_under, list_options
from cua.discovery.run import run_values
from cua.discovery.tools.guard import Result, log, one_at_a_time, resolve_point
from cua.discovery.tools.read_helpers import (
    headings,
    is_header,
    is_word,
    off_table,
    page_texts,
    read_target,
    spot,
    value_in_box,
    where,
)
from cua.safety.redact import IdMask, norm
from cua.vision.look import Element, Look
from cua.vision.table import append_rows, read_rows, same_line, table_columns

Cols = list[tuple[str | None, float, float]]


def _saved_value(
    ctx: Ctx, lk: Look, el: Element, found: tuple[str, str | None], args: dict[str, object]
) -> str:
    """extract_value's body once the box holds the type: save the value, log only where it is."""
    value, pattern = found
    save_as = str(args["save_as"])
    ctx.run.saved[save_as] = value
    values = run_values(ctx.run, ctx.secrets)
    log(
        ctx,
        "extract_value",
        args,
        "saved",
        el.box.center,
        crop(ctx, lk, el.box.center, el),
        page_texts=page_texts(lk, values, el),
        headings=headings(lk, values, el),
        pattern=pattern,
        **read_target(lk, el, values),
    )
    return f"Saved {save_as} = {IdMask.for_site(ctx.site)(value)!r}."  # an id: its last digits


def _make_extract_value(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def extract_value(ref: int, save_as: str, value_type: str, description: str) -> Result:
        """Save a value the goal asked for, read from a numbered box.

        Args:
            ref: Number of the box holding the value, not its header.
            save_as: Name to save it under, e.g. 'savings_balance'.
            value_type: Expected type: 'string', 'integer', 'number', 'currency', 'date', 'phone', 'email' or 'id'.
            description: What the value is, in plain words.
        """  # noqa: E501 (the model reads this docstring verbatim)
        lk = ctx.run.look
        el = lk.get(ref) if lk else None
        if el is None or lk is None:
            return f"STALE: [{ref}] is not in the latest look. Call observe."
        found = value_in_box(el.text, value_type)
        if found is None:
            return f"REFUSED: {el.text!r} holds no {value_type}. Pick the value box, not a header."
        args = {
            "ref": ref,
            "save_as": save_as,
            "value_type": value_type,
            "description": description,
        }
        return _saved_value(ctx, lk, el, found, args)

    return extract_value


def _columns(
    ctx: Ctx, lk: Look, head: Element, save_as: str, columns: list[str]
) -> tuple[Cols, int | None] | None:
    """The table's columns and the header line's bottom (None: scrolled on, the header is gone),
    or None when the asked columns are not on the header's line."""
    if save_as in ctx.run.tables and not any(is_header(head.text, c) for c in columns):
        return ctx.run.tables[save_as], None  # type: ignore[return-value]
    return table_columns(lk, head, columns, is_header)


def _log_table(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, lk: Look, head: Element, args: dict[str, object], cols: Cols, continued: bool
) -> None:
    """The extract_table event: labels and positions only, never a cell."""
    columns, save_as = args["columns"], args["save_as"]
    assert isinstance(columns, list)
    first = next(
        (e for e in lk.elements if same_line(e.box, head.box) and is_header(e.text, columns[0])),
        None,
    )
    rest = off_table(lk, ctx.run.saved[str(save_as)])  # type: ignore[arg-type]
    values = run_values(ctx.run, ctx.secrets)
    log(
        ctx,
        "extract_table",
        args,
        "saved",
        label=columns[0],
        continued=continued,
        header=spot(lk, first) if first else None,
        page_texts=page_texts(rest, values),
        headings=headings(rest, values),
        columns_x=[[lo, hi] for name, lo, hi in cols if name],
    )


def _saved_rows(
    ctx: Ctx,
    lk: Look,
    head: Element,
    found: tuple[Cols, int | None],
    args: dict[str, object],
) -> str:
    """extract_table's body once the columns are found: read the rows under the header, append
    them to the same save_as, log labels only."""
    (cols, below), save_as, row_limit = found, str(args["save_as"]), int(args["row_limit"])  # type: ignore[call-overload]
    old = ctx.run.saved.get(save_as, [])
    rows, more = read_rows(lk, cols, below, row_limit)
    ctx.run.tables[save_as] = cols  # type: ignore[assignment]
    ctx.run.saved[save_as] = append_rows(old, rows)[:row_limit]  # type: ignore[arg-type]
    _log_table(ctx, lk, head, args, cols, below is None)
    total = len(ctx.run.saved[save_as])
    tail = (
        " The table may continue below: scroll and call extract_table again with the same "
        "save_as."
        if more and total < row_limit
        else ""
    )
    return f"Saved {total - len(old)} rows to {save_as} ({total} in all).{tail}"


def _make_extract_table(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def extract_table(  # noqa: PLR0913 (the notebook's own signature; the model reads it)
        header_ref: int, save_as: str, columns: list[str], description: str, row_limit: int = 50
    ) -> Result:
        """Save a table or list the goal asked for: our code reads its rows under the header.

        Args:
            header_ref: Number of one header cell of the table (e.g. its 'Date' header).
            save_as: Name to save the rows under, e.g. 'transactions_1'.
            columns: The header texts of the columns you want, exactly as shown.
            description: What the table is, in plain words.
            row_limit: Most rows to read.
        """
        lk, values = ctx.run.look, run_values(ctx.run, ctx.secrets)
        head = lk.get(header_ref) if lk else None
        if head is None or lk is None:
            return f"STALE: [{header_ref}] is not in the latest look. Call observe."
        if bad := [c for c in columns if not is_word(c, values)]:
            return f"REFUSED: {bad} are not header texts (a header never holds a value)."
        if (found := _columns(ctx, lk, head, save_as, columns)) is None:
            return f"REFUSED: not every one of {columns} is a header on the line of [{header_ref}]."
        args: dict[str, object] = {
            "header_ref": header_ref,
            "save_as": save_as,
            "columns": columns,
            "description": description,
            "row_limit": row_limit,
        }
        return _saved_rows(ctx, lk, head, found, args)

    return extract_table


async def _saved_options(
    ctx: Ctx, lk: Look, point: tuple[int, int], options: list[str], args: dict[str, object]
) -> str:
    """extract_options' body once the dropdown is found: save its options, log only where it is
    (its label, anchor, point and index), never an option. The crop keeps no text (the dropdown
    shows its current option, a value)."""
    save_as = str(args["save_as"])
    ctx.run.saved[save_as] = options
    values = run_values(ctx.run, ctx.secrets) | {norm(o) for o in options}
    log(
        ctx,
        "extract_options",
        args,
        "saved",
        point,
        crop(ctx, lk, point, None),
        index=await dropdown_under(ctx, point),
        page_texts=page_texts(lk, values),
        headings=headings(lk, values),
        **where(lk, point, values),
    )
    return f"Saved {len(options)} options to {save_as}."


def _make_extract_options(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def extract_options(
        save_as: str,
        description: str,
        ref: int | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> Result:
        """Save the list of options of a dropdown the goal asks about. Our code reads them.

        Args:
            save_as: Name to save the list under, e.g. 'from_accounts'.
            description: What the options are, in plain words.
            ref: Number of the dropdown, or leave empty and give x and y.
            x: Pixel x of the dropdown.
            y: Pixel y of the dropdown.
        """
        point = resolve_point(ctx, ref, x, y)
        if isinstance(point, str):
            return point
        lk = ctx.run.look
        assert lk is not None  # resolve_point refused a missing look
        if not (options := await list_options(ctx, point)):
            return f"REFUSED: no dropdown at {point}. Point at the dropdown itself."
        args: dict[str, object] = {"ref": ref, "x": x, "y": y, "save_as": save_as}
        args["description"] = description
        return await _saved_options(ctx, lk, point, options, args)

    return extract_options


def make_read_tools(ctx: Ctx) -> list[BaseTool]:
    """extract_value, extract_table (the notebook's TOOLS order), then extract_options."""
    return [_make_extract_value(ctx), _make_extract_table(ctx), _make_extract_options(ctx)]

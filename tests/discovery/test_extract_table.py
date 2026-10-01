"""extract_table: the agent points at a header, code reads the rows from OCR (live goal 'Log in,
get all transactions per account' saved nothing: extract_value holds one value per box)."""
import ast
import asyncio
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace

from tests.discovery.test_save_artifact import NS, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
SHARED = {"col_of", "same_line", "table_columns", "column_spans", "text_lines", "row_of", "read_rows",
          "append_rows", "like_rows", "cell_shape"}
FNS = SHARED | {"Box", "Element", "Look", "norm", "is_word", "redactor", "_num", "spot",
                "page_texts", "headings", "extract_table", "is_header", "off_table", "saved_texts"}
COLS = ["Date", "Description", "Amount"]
HEADER = [("Date", (100, 100, 140, 120)), ("Description", (250, 100, 350, 120)),
          ("Amount", (500, 100, 560, 120)), ("Account Services", (0, 100, 80, 120))]
ROWS = [("09/01/2026", (96, 130, 180, 150)), ("Funds Transfer Sent", (255, 130, 400, 150)),
        ("$100.00", (507, 130, 560, 150)),
        ("09/02/2026", (104, 160, 188, 180)), ("Bill Payment", (245, 160, 340, 180)),
        ("$25.00", (495, 160, 545, 180))]
FOOTER = [("About Us", (100, 260, 170, 280))]          # 80px below the last row: not in the table


@dataclass
class Handoff:
    look: object = None
    saved: dict = field(default_factory=dict)
    tables: dict = field(default_factory=dict)


def _ns(values: set[str] = frozenset()) -> dict:
    tree = ast.parse(SRC.read_text())
    keep = []
    for n in tree.body:
        if getattr(n, "name", None) in FNS:
            n.decorator_list = [d for d in getattr(n, "decorator_list", [])
                                if ast.unparse(d).startswith("dataclass")]
            keep.append(n)
        elif isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in {"TABLE_GAP", "NUMBER"}:
            keep.append(n)
    events: list[dict] = []
    ns: dict = {"dataclass": dataclass, "replace": replace, "re": re, "run_values": lambda: set(values),
                "__name__": "discovery_table", "HANDOFF": Handoff(), "events": events,
                "log": lambda tool, args, result, point=None, crop=None, **extra: events.append(
                    {"tool": tool, "args": args, "result": result, "point": point, "crop": crop, **extra})}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def _look(ns, items):
    els = tuple(ns["Element"](i, t, ns["Box"](*b)) for i, (t, b) in enumerate(items, 1))
    return ns["Look"](b"", b"", els, "https://parabank.parasoft.com/parabank/activity.htm")


def _read(ns, items, header="Date", cols=COLS, limit=50):
    look = _look(ns, items)
    head = next(e for e in look.elements if e.text == header)
    cols_, below = ns["table_columns"](look, head, cols, ns["is_header"])
    return ns["read_rows"](look, cols_, below, limit)


def test_a_three_column_table_is_read_into_rows_even_when_cells_are_a_few_px_off() -> None:
    rows, more = _read(_ns(), [*HEADER, *ROWS, *FOOTER])
    assert rows == [{"Date": "09/01/2026", "Description": "Funds Transfer Sent", "Amount": "$100.00"},
                    {"Date": "09/02/2026", "Description": "Bill Payment", "Amount": "$25.00"}]
    assert more is False                                   # ended at the gap, not the screen's edge


def test_reading_stops_at_a_vertical_gap() -> None:
    far = [("09/03/2026", (100, 240, 180, 260)), ("$5.00", (500, 240, 540, 260))]
    rows, _ = _read(_ns(), [*HEADER, *ROWS, *far])
    assert len(rows) == 2


def test_a_table_that_runs_to_the_bottom_of_the_screen_may_continue() -> None:
    assert _read(_ns(), [*HEADER, *ROWS])[1] is True


def test_only_the_asked_columns_are_kept_and_the_row_limit_holds() -> None:
    rows, more = _read(_ns(), [*HEADER, *ROWS], header="Amount", cols=["Amount"], limit=1)
    assert rows == [{"Amount": "$100.00"}] and more is False


def test_append_drops_only_the_overlap_of_a_scrolled_second_read() -> None:
    ns = _ns()
    a, b, c = ({"x": "1"}, {"x": "2"}, {"x": "3"})
    assert ns["append_rows"]([a, b], [b, c]) == [a, b, c]
    assert ns["append_rows"]([a, a], [a, a, b]) == [a, a, b]
    assert ns["append_rows"]([], [a]) == [a]


def _tool(ns, items, **kw):
    ns["HANDOFF"].look = _look(ns, items)
    args = {"header_ref": 1, "save_as": "transactions_1", "columns": COLS, "description": "rows", **kw}
    return asyncio.run(ns["extract_table"](**args))


def test_the_tool_saves_rows_and_logs_labels_only() -> None:
    ns = _ns()
    msg = _tool(ns, [*HEADER, *ROWS, *FOOTER])
    assert ns["HANDOFF"].saved["transactions_1"][1]["Description"] == "Bill Payment"
    assert msg.startswith("Saved 2 rows") and "continue below" not in msg
    ev = ns["events"][-1]
    assert ev["tool"] == "extract_table" and ev["label"] == "Date" and ev["args"]["columns"] == COLS
    assert ev["header"]["ordinal"] == 1 and ev["args"]["row_limit"] == 50
    blob = str(ev)
    assert not any(v in blob for v in ("09/01/2026", "Funds Transfer", "$100.00", "Bill Payment", "$25.00"))


def test_a_second_call_with_the_same_name_appends_after_a_scroll() -> None:
    ns = _ns()
    assert "continue below" in _tool(ns, [*HEADER, *ROWS])
    scrolled = [("09/02/2026", (104, 10, 188, 30)), ("Bill Payment", (245, 10, 340, 30)),
                ("$25.00", (495, 10, 545, 30)), ("09/03/2026", (100, 40, 180, 60)),
                ("ATM", (250, 40, 290, 60)), ("$5.00", (500, 40, 540, 60))]
    msg = _tool(ns, scrolled)                              # header gone: the saved columns are used
    assert msg.startswith("Saved 1 rows") and "3 in all" in msg
    assert [r["Description"] for r in ns["HANDOFF"].saved["transactions_1"]] == \
        ["Funds Transfer Sent", "Bill Payment", "ATM"]


def test_a_header_holding_a_run_value_is_refused() -> None:
    ns = _ns({"13566"})
    msg = _tool(ns, [("Account 13566", (100, 100, 200, 120)), ("Amount", (500, 100, 560, 120))],
                columns=["Account 13566", "Amount"])
    assert msg.startswith("REFUSED") and not ns["events"]


def test_columns_not_on_the_header_row_are_refused() -> None:
    ns = _ns()
    assert _tool(ns, [*HEADER, *ROWS], columns=["Date", "Balance"]).startswith("REFUSED")


def test_saved_texts_holds_every_cell_for_evidence_masking() -> None:
    saved = {"b": "$5.00", "t": [{"Date": "09/01/2026", "Amount": "$1.00"}]}
    assert _ns()["saved_texts"](saved) == {"$5.00", "09/01/2026", "$1.00"}


def _table_ev(save_as="transactions_1") -> dict:
    return {**_ev("extract_table", {"header_ref": 1, "save_as": save_as, "columns": COLS,
                                    "description": "rows", "row_limit": 50}, "saved", label="Date"),
            "header": {"text": "Date", "ordinal": 1}, "crop": None,
            "url": "https://parabank.parasoft.com/parabank/activity.htm", "page_texts": ["Account Activity"],
            "headings": ["Account Activity"]}


def test_build_capability_accepts_a_table_only_run() -> None:
    cap = NS["build_capability"]([START, _table_ev()], _meta(name="transactions"))
    step = cap.steps[0]
    assert step.action == "extract_table" and step.header.label == "Date" and step.columns == COLS
    assert cap.outputs[0].type == "table" and cap.outputs[0].columns == COLS
    assert cap.checkpoint == "Account Activity"


def test_a_continued_table_is_one_step() -> None:
    scroll = _ev("scroll", {"direction": "down"}, "Scrolled down.")
    cap = NS["build_capability"]([START, _table_ev(), scroll, _table_ev()], _meta(name="t"))
    assert [s.action for s in cap.steps] == ["extract_table"] and len(cap.outputs) == 1


def test_one_table_per_account_is_one_output_each() -> None:
    cap = NS["build_capability"]([START, _table_ev("transactions_1"), _table_ev("transactions_2")],
                                 _meta(name="t"))
    assert [o.name for o in cap.outputs] == ["transactions_1", "transactions_2"]


def test_the_prompt_names_extract_table_for_lists() -> None:
    text = SRC.read_text()
    prompt = " ".join(text[text.index("VISUAL_SYSTEM_PROMPT = "):].split())
    assert "every list or table with extract_table (not extract_value)" in prompt
    assert "save_as name_1, name_2" in prompt


def test_describe_names_the_table_outputs() -> None:
    seen = []

    class Model:
        def with_structured_output(self, kind):
            return SimpleNamespace(ainvoke=lambda prompt: _done(seen, prompt))

    async def _done(out, prompt):
        out.append(prompt)
    ns = {**NS, "MODEL": Model()}
    exec(compile(ast.Module([n for n in ast.parse(SRC.read_text()).body
                             if getattr(n, "name", None) == "describe"], []), str(SRC), "exec"), ns)
    asyncio.run(ns["describe"]("goal", [START, _table_ev("transactions_1")]))
    assert "Tables it returns (rows): transactions_1." in seen[0]


def test_the_footer_and_menu_links_below_the_table_are_never_rows() -> None:
    """Live run: the page footer ('Home | About Us I Services …', '© Parasoft …') sat less than
    TABLE_GAP under the last row and was read as two more transactions."""
    footer = [("Home | About Us I Services | Products I Locations", (240, 190, 480, 208)),
              ("Contact Us", (500, 190, 560, 208)),
              ("© Parasoft. All rights reserved. Visit us at:www.parasoft.com", (96, 214, 400, 232))]
    rows, more = _read(_ns(), [*HEADER, *ROWS, *footer])
    assert [r["Date"] for r in rows] == ["09/01/2026", "09/02/2026"]
    assert more is False


def test_a_line_that_breaks_a_columns_shape_ends_the_table() -> None:
    odd = [("Total", (100, 190, 140, 208)), ("$125.00", (500, 190, 560, 208))]   # 'Total' is not a date
    rows, _ = _read(_ns(), [*HEADER, *ROWS, *odd])
    assert len(rows) == 2


def test_rows_with_an_empty_cell_are_still_rows() -> None:
    more = [("09/03/2026", (100, 190, 180, 208)), ("Funds Transfer Received", (250, 190, 420, 208))]
    rows, _ = _read(_ns(), [*HEADER, *ROWS, *more])
    assert len(rows) == 3 and "Amount" not in rows[2]

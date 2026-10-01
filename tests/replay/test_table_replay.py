"""do_extract_table: find the header by its label, read the rows with discovery's own function."""
import ast
import asyncio
import json
from pathlib import Path

import pytest

from tests.discovery.test_extract_table import COLS, FOOTER, HEADER, ROWS, SHARED

DISCOVERY = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
REPLAY = Path(__file__).parents[2] / "notebooks/replay/replay.py"
WANT = [{"Date": "09/01/2026", "Description": "Funds Transfer Sent", "Amount": "$100.00"},
        {"Date": "09/02/2026", "Description": "Bill Payment", "Amount": "$25.00"}]


def _defs(path: Path) -> dict[str, str]:
    body = ast.parse(path.read_text()).body
    out = {n.name: ast.unparse(n) for n in body if getattr(n, "name", None) in SHARED}
    gap = next(n for n in body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TABLE_GAP")
    return {**out, "TABLE_GAP": ast.literal_eval(gap.value)}


def test_the_table_reader_is_identical_to_discoverys() -> None:
    assert _defs(REPLAY) == _defs(DISCOVERY) and set(_defs(REPLAY)) == SHARED | {"TABLE_GAP"}


def _cap(ns, **step):
    s = {"action": "extract_table", "header": {"label": "Date"}, "columns": COLS, "save_as": "transactions_1", **step}
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=[s], checkpoint="Account Activity",
                            outputs=[{"name": "transactions_1", "type": "table", "description": "rows",
                                      "columns": COLS}])


def _run(ns, mk_look, looks, **step):
    """Each scroll shows the next look."""
    queue = list(looks)
    ns["STATE"].look = mk_look(queue.pop(0))

    async def act(*steps):
        ns["STATE"].look = mk_look(queue.pop(0)) if queue else ns["STATE"].look
        return ns["STATE"].look
    ns["act"], ns["page"] = act, type("P", (), {"mouse": type("M", (), {"wheel": lambda *a: None})()})()
    cap = _cap(ns, **step)
    return asyncio.run(ns["do_extract_table"](cap.steps[0], None, cap))


def test_replay_reads_the_fixture_into_the_same_rows(ns, mk_look) -> None:
    assert _run(ns, mk_look, [[*HEADER, *ROWS, *FOOTER]]) is True
    assert ns["STATE"].outputs["transactions_1"] == WANT


def test_an_empty_table_is_a_valid_output(ns, mk_look) -> None:
    assert _run(ns, mk_look, [[*HEADER, *FOOTER]]) is True
    assert ns["STATE"].outputs["transactions_1"] == []


def test_a_missing_header_is_a_failed_check(ns, mk_look) -> None:
    assert _run(ns, mk_look, [FOOTER]) is False and "transactions_1" not in ns["STATE"].outputs


def test_a_table_past_the_screen_is_read_on_after_a_scroll(ns, mk_look) -> None:
    more = [("09/02/2026", (104, 10, 188, 30)), ("Bill Payment", (245, 10, 340, 30)),
            ("$25.00", (495, 10, 545, 30)), ("09/03/2026", (100, 40, 180, 60)),
            ("ATM", (250, 40, 290, 60)), ("$5.00", (500, 40, 540, 60)), *FOOTER]
    assert _run(ns, mk_look, [[*HEADER, *ROWS], more]) is True
    assert [r["Description"] for r in ns["STATE"].outputs["transactions_1"]] == \
        ["Funds Transfer Sent", "Bill Payment", "ATM"]


def test_the_row_limit_holds(ns, mk_look) -> None:
    assert _run(ns, mk_look, [[*HEADER, *ROWS]], row_limit=1) is True
    assert ns["STATE"].outputs["transactions_1"] == WANT[:1]


def test_a_table_step_needs_no_target(ns) -> None:
    cap = _cap(ns)
    assert getattr(cap.steps[0], "target", None) is None and "extract_table" in ns["ACTIONS"]
    assert ns["read_only_done"](cap, []) is True


def test_the_outputs_line_shows_rows(ns) -> None:
    res = ns["ReplayResult"]("SUCCESS", {"transactions_1": WANT}, [])
    assert "Bill Payment" in res.outputs_line


def test_evidence_masks_every_cell(ns, tmp_path) -> None:
    from test_load_inputs import CAP, _write
    ns["LAST_RUN"].update(values=set(), final=None)
    res = ns["ReplayResult"]("SUCCESS", {"transactions_1": WANT, "balance": "$5.00"}, [])
    folder = ns["save_evidence"](res, _write(tmp_path, CAP), tmp_path / "out")
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["outputs"] == {"transactions_1": [{c: "***" for c in COLS}] * 2, "balance": "***"}
    assert "Bill Payment" not in (folder / "summary.json").read_text()


@pytest.mark.parametrize("rows", [[], WANT])
def test_masked_outputs_keep_the_shape(ns, rows) -> None:
    assert ns["masked_outputs"]({"t": rows}) == {"t": [{c: "***" for c in r} for r in rows]}

"""What the tools log, compiled: read-only runs, tables, labels joined to values, and dropdown
selects. The recorder halves of the old tool tests.

Ported from tests/discovery/test_read_runs.py, test_extract_table.py, test_label_values.py and
test_select_anchor.py (their build_capability/save_artifact cases), now importing the package.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cua.discovery.recorder import (
    build_capability,
    crops_for,
    describe,
    flag_leaks,
    input_name,
    save_artifact,
)
from cua.discovery.tools.read_helpers import read_target, where
from cua.schema import Select
from tests.fakes import COLS, make_look
from tests.unit.discovery.recorder.test_recorder import SENT, START, _ev, _FakeModel, _meta
from tests.unit.discovery.tools.test_read import BALANCE, OVERVIEW

ACTIVITY = "https://parabank.parasoft.com/parabank/activity.htm"
TRANSFER = "https://parabank.parasoft.com/parabank/transfer.htm"
LOGIN_PAGE = ["ParaBank", "Customer Login", "Username", "Password", "Forgot login info?"]
READ_PAGE = [
    "ParaBank",
    "Account Services",
    "Transfer Funds",
    "Account Details",
    "Account Number:",
    "Balance*",
    "Available:",
]


def _read_log(proof: str, page: list[str] = READ_PAGE) -> list[dict]:
    args = {"ref": 4, "save_as": "balance", "value_type": "currency", "description": "Balance"}
    extract = {
        **_ev("extract_value", args, "saved", label="Balance*"),
        "url": ACTIVITY,
        "page_texts": page,
        "table": None,
    }
    return [
        {**START, "start_texts": LOGIN_PAGE},
        extract,
        _ev("finish_business_outcome", {"outcome": "read", "proof_text": proof}, "OK"),
        _ev(
            "click",
            {"ref": 9, "x": None, "y": None},
            "Clicked 'Log Out'.",
            own="Log Out",
            text="Log Out",
        ),
    ]


# --- read-only runs (live: view_account_details_and_transactions) ---


def test_a_read_after_logout_takes_its_checkpoint_from_the_page_it_read() -> None:
    meta = _meta(name="read", success_text="Customer Login")
    cap = build_capability(_read_log("Customer Login"), meta)  # type: ignore[arg-type]
    assert cap.checkpoint == "Balance*"  # the value's own label, on that page


def test_an_agent_proof_on_the_read_page_is_kept() -> None:
    cap = build_capability(_read_log("Account Details"), _meta(name="r"))  # type: ignore[arg-type]
    assert cap.checkpoint == "Account Details"


def test_text_also_on_the_start_page_is_never_the_checkpoint() -> None:
    log = _read_log("Customer Login", page=["ParaBank", "Customer Login", "Account Details"])
    log[1]["label"] = "ParaBank"
    assert build_capability(log, _meta(name="r")).checkpoint == "Account Details"  # type: ignore[arg-type]


def test_a_page_text_holding_a_run_value_is_dropped_before_the_save() -> None:
    log = _read_log("Customer Login", page=["Account 13566", "Balance*"])
    flag_leaks(log, {"13566"})  # type: ignore[arg-type]
    assert log[1]["page_texts"] == ["Balance*"]
    assert not log[1].get("leak")


def test_a_send_still_takes_the_pages_response() -> None:
    click = _ev(
        "click",
        {"ref": 8, "x": None, "y": None},
        "Clicked 'Transfer'.",
        own="TRANSFER",
        text="TRANSFER",
        landed=["Transfer Complete!"],
    )
    log = [*_read_log("Customer Login")[:2], click]
    assert build_capability(log, _meta(name="t")).checkpoint == "Transfer Complete!"  # type: ignore[arg-type]


def test_a_read_with_no_recorded_page_keeps_the_old_rule() -> None:
    """An event with no page_texts (an older log) proves nothing: the proof is kept."""
    log = _read_log("Accounts Overview")
    del log[1]["page_texts"]
    assert build_capability(log, _meta(name="r")).checkpoint == "Accounts Overview"  # type: ignore[arg-type]


def test_it_saves_as_an_anchored_extract_on_the_balance_header() -> None:
    look = make_look(OVERVIEW, ACTIVITY)
    el = look.elements[BALANCE]
    args = {"ref": 10, "save_as": "first_balance", "value_type": "currency", "description": "b"}
    ev = {
        **_ev("extract_value", args, "saved"),
        "point": el.box.center,
        **read_target(look, el, set()),
    }
    step = build_capability([START, ev], _meta(name="bal")).steps[0]  # type: ignore[list-item]
    assert step.target.table_cell is None  # type: ignore[union-attr]
    assert step.target.ocr_text is None  # type: ignore[union-attr]
    assert step.target.anchor.label == "Balance*"  # type: ignore[union-attr]
    assert step.target.anchor.ordinal == 1  # type: ignore[union-attr]
    assert "202484" not in str(step)
    assert "13566" not in str(step)


# --- tables ---


def _table_ev(save_as: str = "transactions_1") -> dict:
    args = {
        "header_ref": 1,
        "save_as": save_as,
        "columns": COLS,
        "description": "rows",
        "row_limit": 50,
    }
    return {
        **_ev("extract_table", args, "saved", label="Date"),
        "header": {"text": "Date", "ordinal": 1},
        "crop": None,
        "url": ACTIVITY,
        "page_texts": ["Account Activity"],
        "headings": ["Account Activity"],
    }


def test_build_capability_accepts_a_table_only_run() -> None:
    cap = build_capability([START, _table_ev()], _meta(name="transactions"))  # type: ignore[list-item]
    step = cap.steps[0]
    assert step.action == "extract_table"
    assert step.header.label == "Date"  # type: ignore[union-attr]
    assert step.columns == COLS  # type: ignore[union-attr]
    assert cap.outputs[0].type == "table"
    assert cap.outputs[0].columns == COLS
    assert cap.checkpoint == "Account Activity"


def test_a_continued_table_is_one_step() -> None:
    scroll = _ev("scroll", {"direction": "down"}, "Scrolled down.")
    log = [START, _table_ev(), scroll, _table_ev()]
    cap = build_capability(log, _meta(name="t"))  # type: ignore[arg-type]
    assert [s.action for s in cap.steps] == ["extract_table"]
    assert len(cap.outputs) == 1


def test_one_table_per_account_is_one_output_each() -> None:
    log = [START, _table_ev("transactions_1"), _table_ev("transactions_2")]
    cap = build_capability(log, _meta(name="t"))  # type: ignore[arg-type]
    assert [o.name for o in cap.outputs] == ["transactions_1", "transactions_2"]


# --- labels joined to values (live: transfer_money_between_accounts) ---


def _where(values: set[str], *texts: tuple[str, tuple[int, int, int, int]], at=(300, 70)) -> dict:  # type: ignore[no-untyped-def]
    return where(make_look(list(texts), "u"), at, values)


def test_a_sent_value_joined_to_a_label_is_cut_from_it_and_from_the_input_name() -> None:
    got = _where({"16785"}, ("to account #16785", (10, 60, 200, 80)))
    assert got["label"] == "to account #"
    assert got["anchor"]["text"] == "to account #"
    assert input_name(got["label"]) == "to_account"
    assert "16785" not in str(got)


@pytest.mark.parametrize(
    ("ocr", "label"),
    [
        ("From account #[", "From account #"),
        ("]to account #[", "to account #"),
        ("| Amount: $", "Amount: $"),
    ],
)
def test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(ocr: str, label: str) -> None:
    assert _where(set(), (ocr, (10, 60, 200, 80)))["label"] == label


def test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest() -> None:
    got = _where(
        {"16785"},
        ("Transfer to", (10, 20, 120, 40)),
        ("[16785]", (10, 60, 120, 80)),
        at=(200, 70),
    )
    assert got["label"] == "Transfer to"


def test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label() -> None:
    merged = ("to account #|15120", (720, 345, 840, 365))  # centre (780, 355)
    got = _where({"15120"}, ("From account #", (484, 345, 586, 365)), merged, at=(800, 355))
    assert got["label"] == "to account #"
    assert got["anchor"]["text"] == "to account #"
    assert got["offset"] == [20, 0]
    assert "15120" not in str(got)


def test_a_plain_word_under_the_point_is_still_never_the_anchor() -> None:
    """A box's own text with nothing cut from it (a value, a button) stays off the anchor."""
    assert "anchor" not in _where(set(), ("Checking", (760, 345, 840, 365)), at=(800, 355))


@pytest.mark.parametrize("where_it_hides", ["label", "hint", "own"])
def test_a_value_inside_a_label_refuses_the_save(where_it_hides: str) -> None:
    text = "to account #16785"
    ev = _ev(
        "select_option",
        {"hint": text if where_it_hides == "hint" else "to account #"},
        "Selected.",
        label=text if where_it_hides == "label" else "to account #",
        own=text if where_it_hides == "own" else None,
        url=TRANSFER,
    )
    log = [START, ev]
    flag_leaks(log, {"16785"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="value typed this run") as err:
        build_capability(log, _meta(name="transfer"))  # type: ignore[arg-type]
    assert "16785" not in str(err.value)


def test_a_number_that_only_resembles_a_value_is_not_a_leak() -> None:
    log = [START, _ev("select_option", {}, "Selected.", label="to account #", url=TRANSFER)]
    flag_leaks(log, {"167", "account 1"})  # type: ignore[arg-type]
    assert not log[1].get("leak")


# --- dropdown selects ---


def _select(label: str, point: tuple[int, int], **extra: object) -> dict:
    args = {"ref": 5, "x": None, "y": None}
    return {
        **_ev("select_option", args, "Selected.", label=label, url=TRANSFER),
        "point": point,
        **extra,
    }


def test_the_agents_select_and_the_same_sent_dropdown_are_one_step() -> None:
    """Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #') were 4
    selects."""
    click = _ev(
        "click",
        {"ref": 8, "x": None, "y": None},
        "Clicked 'Transfer'.",
        own="TRANSFER",
        text="TRANSFER",
        landed=["Transfer Complete!"],
    )
    log = [
        START,
        _select("From account #[", (560, 300)),
        _select("]to account #[", (560, 340)),
        _select("From account #", (620, 300), dropdown=True, field_box=[540, 290, 700, 310]),
        _select("to account #", (620, 340), dropdown=True, field_box=[540, 330, 700, 350]),
        SENT,
        {**click, "url": TRANSFER},
    ]
    cap = build_capability(log, _meta(name="transfer"))  # type: ignore[arg-type]
    assert [s.action for s in cap.steps] == ["select", "select", "click"]
    labels = [s.target.anchor.label for s in cap.steps[:2]]  # type: ignore[union-attr]
    assert labels == ["From account #", "to account #"]


def test_two_dropdowns_far_apart_with_one_label_stay_two_steps() -> None:
    log = [START, _select("Account", (560, 300)), _select("Account", (560, 500)), SENT]
    assert len(build_capability(log, _meta(name="t")).steps) == 2  # type: ignore[arg-type]  # noqa: PLR2004


def test_the_select_step_keeps_the_dropdowns_index(tmp_path: Path) -> None:
    log = [START, _select("to account #", (300, 200), index=1), SENT]
    cap = build_capability(log, _meta(name="t"))  # type: ignore[arg-type]
    assert cap.steps[0].index == 1  # type: ignore[union-attr]
    path = save_artifact(cap, crops_for(log, cap), tmp_path)  # type: ignore[arg-type]
    assert yaml.safe_load(path.read_text())["steps"][0]["index"] == 1


def test_an_old_select_without_an_index_still_loads() -> None:
    step = Select(option="{{a}}", target={"anchor": {"label": "a", "offset": [0, 0]}})  # type: ignore[arg-type]
    assert step.index is None


def test_a_select_with_no_anchor_is_refused_not_saved() -> None:
    ev = _select("to account #", (300, 200), index=1)
    for k in ("anchor", "label", "offset"):
        ev.pop(k)
    ev["args"] = {"hint": "option"}
    with pytest.raises(ValueError, match="no label to find it by") as err:
        build_capability([START, ev, SENT], _meta(name="t"))  # type: ignore[list-item]
    assert "Re-run discovery" in str(err.value)


@pytest.mark.asyncio
async def test_describe_names_the_table_outputs() -> None:
    model = _FakeModel()
    await describe("goal", [START, _table_ev("transactions_1")], model)  # type: ignore[list-item]
    assert "Tables it returns (rows): transactions_1." in model.prompts[0]

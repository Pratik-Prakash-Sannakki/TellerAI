"""The checkpoint is text that names the final screen and stays the same between runs: never a
value (an amount, a date, an id, a typed value), never a lone form label or a single word, and
preferably text new on the final screen (not on an earlier screen of the run).

Live cases: 'Total $5022.93' (a balance, changed after a payment), 'City:' (a label also on
earlier pages), 'Account' (a single word on every logged-in page).
"""

from __future__ import annotations

import json
from pathlib import Path

from cua.discovery.recorder import build_capability, checkpoint
from cua.discovery.recorder.checkpoint import WARNING, stable
from tests.unit.discovery.recorder.test_recorder import START, _ev, _meta

LOGIN_PAGE = ["Customer Login", "Username", "Password", "© Parasoft. All rights reserved."]
MENU = ["Account Services", "Accounts Overview", "Transfer Funds", "Bill Pay", "Log Out"]
OVERVIEW = [
    *MENU,
    "Account",
    "Balance*",
    "Total $5022.93",
    "*Balance includes deposits that may be subject to holds",
]


def _start(counts: dict[str, int] | None = None, looks: int = 0) -> dict:
    return {**START, "start_texts": LOGIN_PAGE, "looks": looks, "text_counts": counts or {}}


def _read(page: list[str], headings: list[str] | None = None, label: str = "Account") -> dict:
    args = {
        "header_ref": 1,
        "save_as": "t",
        "columns": ["Account"],
        "description": "rows",
        "row_limit": 50,
    }
    return {**_ev("extract_table", args, "saved", label=label), "page_texts": page,
            "headings": headings or []}  # fmt: skip


def _click(from_texts: list[str], landed: list[str] | None = None) -> dict:
    ev = _ev("click", {"ref": 1, "x": None, "y": None}, "Clicked.", own="Go", text="Go")
    return {**ev, "from_texts": from_texts, **({"landed": landed} if landed else {})}


def _proof(text: str) -> dict:
    return _ev("finish_business_outcome", {"outcome": "x", "proof_text": text}, "OK")


def test_a_balance_line_is_never_the_checkpoint() -> None:
    """Live: every text but the total was on half the looks, so 'Total $5022.93' was picked."""
    counts = {"total $5022.93": 3, **{t.casefold(): 4 for t in OVERVIEW if "$" not in t}}
    log = [_start(counts, looks=8), _read(OVERVIEW, headings=["Account", "Balance*", "Log Out"])]
    got = checkpoint(log, "Accounts Overview")  # type: ignore[arg-type]
    assert got == "*Balance includes deposits that may be subject to holds"


def test_a_lone_label_is_never_the_checkpoint() -> None:
    page = [*MENU, "Bill Payment Service", "Payee Name:", "City:", "Amount: $"]
    log = [_start(), _read(page, headings=["City:", "Payee Name:"], label="Amount: $")]
    assert checkpoint(log, "x") == "Bill Payment Service"  # type: ignore[arg-type]


def test_a_single_word_is_never_the_checkpoint() -> None:
    log = [_start(), _read(["Account", "Balance*", "Accounts Overview"], headings=["Account"])]
    assert checkpoint(log, "x") == "Accounts Overview"  # type: ignore[arg-type]


def test_text_on_an_earlier_screen_is_not_preferred() -> None:
    """The menu was on the page before the last click; the page's own heading is new."""
    earlier = _click([*MENU, "Welcome to Account Services"])
    page = [*MENU, "Welcome to Account Services", "Bill Payment Service"]
    log = [_start(), earlier, _read(page, headings=["Welcome to Account Services"])]
    assert checkpoint(log, "x") == "Bill Payment Service"  # type: ignore[arg-type]


def test_a_new_heading_after_a_send_is_chosen() -> None:
    sent = _click(MENU, landed=["Bill Payment Complete", "See Account Activity for more details."])
    assert checkpoint([_start(), sent], "x") == "Bill Payment Complete"  # type: ignore[arg-type]
    sent = _click(MENU, landed=["Transfer Complete!"])
    assert checkpoint([_start(), sent], "x") == "Transfer Complete!"  # type: ignore[arg-type]


def test_a_response_label_is_skipped_for_the_next_stable_text() -> None:
    sent = _click(MENU, landed=["Amount:", "Loan Request Processed"])
    assert checkpoint([_start(), sent], "x") == "Loan Request Processed"  # type: ignore[arg-type]


def test_a_text_holding_a_typed_value_is_never_the_checkpoint() -> None:
    page = [*MENU, "Paid to Acme Water", "Bill Payment Complete"]
    log = [_start(), _read(page, headings=["Paid to Acme Water", "Bill Payment Complete"])]
    assert checkpoint(log, "x", {"acme water"}) == "Bill Payment Complete"  # type: ignore[arg-type]


def test_the_models_proof_is_validated_too() -> None:
    log = [_start(), _proof("Total $5022.93"), _proof("Accounts Overview")]
    assert checkpoint(log, "Balance: $10") == "Accounts Overview"  # type: ignore[arg-type]
    assert checkpoint([_start(), _proof("City:")], "Accounts Overview") == "Accounts Overview"  # type: ignore[arg-type]


def test_with_nothing_stable_the_old_pick_is_kept_and_a_warning_logged() -> None:
    log = [_start(), _read(["City:", "Account"], headings=["City:"])]
    assert checkpoint(log, "x") == "City:"  # type: ignore[arg-type]
    warns = [ev for ev in log if ev["tool"] == "warning"]
    assert len(warns) == 1
    assert "checkpoint" in warns[0]["result"]
    assert "City" not in str(warns[0])  # the log names no text from the page


def test_build_capability_passes_the_run_values_on() -> None:
    page = [*MENU, "Paid to Acme Water", "Bill Payment Complete"]
    log = [_start(), _read(page, headings=["Paid to Acme Water"])]
    cap = build_capability(log, _meta(name="p"), {"acme water"})  # type: ignore[arg-type]
    assert cap.checkpoint == "Bill Payment Complete"


def test_with_nothing_new_a_stable_text_is_kept_and_a_warning_logged() -> None:
    """Live: a read on a page whose own texts were all on an earlier screen (only the menu)."""
    log = [_start(), _click(MENU), _read([*MENU, "City:"], headings=["City:"])]
    assert checkpoint(log, "x") in MENU  # type: ignore[arg-type]
    assert [ev["result"] for ev in log if ev["tool"] == "warning"] == [WARNING]


# Live (20261003T023017Z, read-only balances): OCR read the footer link bar differently per look
# ('|' vs 'I'), so exact matching saw it as new, and it was picked.
LIVE = (
    Path(__file__).parents[4]
    / "evidence/discovery/20261003T023017Z-log_in_and_get_the_balance_of_every_acco/events.jsonl"
)
FOOTER = "Home | About Us I Services I Products I Locations I Forum | Site Map I Contact Us"


def test_the_live_balances_run_never_picks_the_footer_link_bar() -> None:
    log = [json.loads(line) for line in LIVE.read_text().splitlines()]
    log = [ev for ev in log if ev["tool"] != "warning"]
    got = checkpoint(log, "x")
    assert got == "*Balance includes deposits that may be subject to holds"


def test_an_ocr_variant_of_a_start_page_text_counts_as_seen() -> None:
    """'Welcome I Home' on the start page, 'Welcome l Home' on the final screen: the same text,
    so never the checkpoint, even when nothing else on the screen is new."""
    start = {**_start(), "start_texts": [*LOGIN_PAGE, "Welcome to the Bank I Home Page"]}
    earlier = _click([*MENU, "Account Services Menu"])
    page = ["Welcome to the Bank l Home Page", "Account Services Menu"]
    log = [start, earlier, _read(page, headings=page)]
    assert checkpoint(log, "x") == "Account Services Menu"  # type: ignore[arg-type]


def test_an_ocr_variant_of_an_earlier_screen_text_is_not_new() -> None:
    """'I' read as 'l' is not a new word: 'Bill Pay Service' (one new word) is the new text."""
    earlier = _click([*MENU, "Welcome to Account Services I Home"])
    page = [*MENU, "Welcome to Account Services l Home", "Bill Pay Service"]
    log = [_start(), earlier, _read(page, headings=["Welcome to Account Services l Home"])]
    assert checkpoint(log, "x") == "Bill Pay Service"  # type: ignore[arg-type]


def test_a_link_bar_is_never_the_checkpoint() -> None:
    assert not stable()(FOOTER)
    assert not stable()("Home | About Us")
    assert not stable()("Home I About Us I Services")
    assert stable()("Bill Payment Service")
    log = [_start(), _read([FOOTER, "Bill Payment Service"], headings=[FOOTER])]
    assert checkpoint(log, "x") == "Bill Payment Service"  # type: ignore[arg-type]

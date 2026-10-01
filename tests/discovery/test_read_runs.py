"""Read-only runs (live: view_account_details_and_transactions): the checkpoint comes from the page
the values were read on, never the login page after logout; a table cell needs a real table."""
import ast
import re
from dataclasses import dataclass, replace
from pathlib import Path

from tests.discovery.test_save_artifact import NS, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
ACTIVITY = "https://parabank.parasoft.com/parabank/activity.htm"
LOGIN_PAGE = ["ParaBank", "Customer Login", "Username", "Password", "Forgot login info?"]
READ_PAGE = ["ParaBank", "Account Services", "Transfer Funds", "Account Details",
             "Account Number:", "Balance*", "Available:"]


def _read_log(proof: str, page: list[str] = READ_PAGE) -> list[dict]:
    extract = {**_ev("extract_value", {"ref": 4, "save_as": "balance", "value_type": "currency",
                                       "description": "Balance"}, "saved", label="Balance*"),
               "url": ACTIVITY, "page_texts": page, "table": None}
    return [{**START, "start_texts": LOGIN_PAGE}, extract,
            _ev("finish_business_outcome", {"outcome": "read", "proof_text": proof}, "OK"),
            _ev("click", {"ref": 9, "x": None, "y": None}, "Clicked 'Log Out'.", own="Log Out",
                text="Log Out")]


def test_a_read_after_logout_takes_its_checkpoint_from_the_page_it_read() -> None:
    cap = NS["build_capability"](_read_log("Customer Login"), _meta(name="read",
                                                                   success_text="Customer Login"))
    assert cap.checkpoint == "Balance*"                    # the value's own label, on that page


def test_an_agent_proof_on_the_read_page_is_kept() -> None:
    assert NS["build_capability"](_read_log("Account Details"), _meta(name="r")).checkpoint \
        == "Account Details"


def test_text_also_on_the_start_page_is_never_the_checkpoint() -> None:
    log = _read_log("Customer Login", page=["ParaBank", "Customer Login", "Account Details"])
    log[1]["label"] = "ParaBank"
    assert NS["build_capability"](log, _meta(name="r")).checkpoint == "Account Details"


def test_a_page_text_holding_a_run_value_is_dropped_before_the_save() -> None:
    log = _read_log("Customer Login", page=["Account 13566", "Balance*"])
    NS["flag_leaks"](log, {"13566"})
    assert log[1]["page_texts"] == ["Balance*"] and not log[1].get("leak")


def test_a_send_still_takes_the_pages_response() -> None:
    log = [*_read_log("Customer Login")[:2],
           _ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Transfer'.", own="TRANSFER",
               text="TRANSFER", landed=["Transfer Complete!"])]
    assert NS["build_capability"](log, _meta(name="t")).checkpoint == "Transfer Complete!"


TABLE_FNS = {"Box", "Element", "Look", "table_cell", "row_block", "column_header", "is_word",
             "read_target", "where", "merged_label", "label_near", "element_at", "spot", "clean_label", "redactor",
             "_num", "norm"}


def _ns(values: set[str] = frozenset()) -> dict:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in TABLE_FNS
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in
                {"TABLE_GAP", "KEY_REACH", "NUMBER"})]
    ns: dict = {"dataclass": dataclass, "replace": replace, "re": re, "run_values": lambda: set(values),
                "__name__": "discovery_table"}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def _look(ns, texts):
    els = tuple(ns["Element"](i, t, ns["Box"](*b)) for i, (t, b) in enumerate(texts, 1))
    return ns["Look"](b"", b"", els, ACTIVITY), els


def _cell(*texts: tuple[str, tuple[int, int, int, int]], value: str) -> dict | None:
    ns = _ns()
    look, els = _look(ns, texts)
    return ns["table_cell"](look, next(e for e in els if e.text == value))


# ParaBank's Accounts Overview, shaped from the live run: a left menu level with the grid.
OVERVIEW = [("Account Services", (20, 200, 170, 218)), ("Accounts Overview", (330, 200, 500, 222)),
            ("Open New Account", (20, 236, 150, 252)), ("Account", (330, 236, 390, 252)),
            ("Balance*", (560, 236, 625, 252)), ("Available Amount", (800, 236, 930, 252)),
            ("Transfer Funds", (20, 262, 130, 278)), ("13566", (330, 262, 380, 278)),
            ("-$202484.50", (560, 262, 660, 278)), ("$0.00", (800, 262, 845, 278)),
            ("Bill Pay", (20, 288, 80, 304)), ("Total", (330, 288, 370, 304)),
            ("-$202484.50", (560, 288, 660, 304))]
BALANCE = 8                                   # the first data row's balance


def test_the_first_accounts_balance_never_uses_the_menu_or_the_title() -> None:
    """Live: row_key 'Transfer Funds' (menu), column 'Accounts Overview' (title); replay read 13566."""
    ns = _ns()
    look, els = _look(ns, OVERVIEW)
    balance = els[BALANCE]
    got = ns["read_target"](look, balance)
    assert got["table"] is None                  # the row key would be an account number: a value
    assert got["label"] == "Balance*" and got["anchor"]["text"] == "Balance*"
    assert got["anchor"]["ordinal"] == 1
    for chrome in ("Transfer Funds", "Accounts Overview", "Account Services"):
        assert chrome not in str(got)
    hx, hy = ns["Box"](*got["anchor"]["box"]).center      # replay's rung 2: header + offset
    assert balance.box.contains(hx + got["offset"][0], hy + got["offset"][1])


def test_it_saves_as_an_anchored_extract_on_the_balance_header() -> None:
    ns = _ns()
    look, els = _look(ns, OVERVIEW)
    ev = {**_ev("extract_value", {"ref": 10, "save_as": "first_balance", "value_type": "currency",
                                  "description": "first balance"}, "saved"),
          "point": els[BALANCE].box.center, **ns["read_target"](look, els[BALANCE])}
    step = NS["build_capability"]([START, ev], _meta(name="bal")).steps[0]
    assert step.target.table_cell is None and step.target.ocr_text is None
    assert step.target.anchor.label == "Balance*" and step.target.anchor.ordinal == 1
    assert "202484" not in str(step) and "13566" not in str(step)


def test_a_nav_link_and_a_banner_are_not_a_table() -> None:
    """Live: available_amount got row_key 'Transfer Funds', column 'Welcome to Account Services'."""
    assert _cell(("Welcome to Account Services", (400, 100, 700, 120)),
                 ("Transfer Funds", (20, 300, 130, 320)), ("Available:", (300, 300, 380, 320)),
                 ("$515.50", (420, 300, 490, 320)), value="$515.50") is None


GRID = [("Account Services", (20, 170, 160, 190)), ("Account Types", (400, 170, 540, 192)),
        ("Open New Account", (20, 200, 150, 216)), ("Type", (400, 200, 440, 216)),
        ("Balance", (600, 200, 660, 216)),
        ("Transfer Funds", (20, 226, 130, 242)), ("Checking", (400, 226, 470, 242)),
        ("$100.00", (600, 226, 670, 242)),
        ("Bill Pay", (20, 252, 80, 268)), ("Savings", (400, 252, 465, 268)),
        ("$25.00", (600, 252, 655, 268))]


def test_a_menu_as_far_from_the_grid_as_its_columns_are_is_unsure() -> None:
    """Menu gap == column gap: nothing tells them apart, so no row key (the anchor is used)."""
    assert _cell(*OVERVIEW, value="$0.00") is None


def test_a_real_grid_gives_its_own_row_key_and_nearest_header() -> None:
    assert _cell(*GRID, value="$25.00") == {"row_key": "Savings", "column": "Balance"}
    assert _cell(*GRID, value="$100.00") == {"row_key": "Checking", "column": "Balance"}


def test_a_row_key_that_is_a_number_or_a_run_value_is_no_key() -> None:
    grid = [*GRID[:9], ("14454", (400, 252, 450, 268)), GRID[10]]
    assert _cell(*grid, value="$25.00") is None
    ns = _ns({"savings"})
    look, els = _look(ns, GRID)
    assert ns["table_cell"](look, els[10]) is None


def test_a_header_far_above_the_value_is_not_its_column() -> None:
    assert _cell(("Type", (300, 100, 340, 120)), ("Amount", (420, 100, 490, 120)),
                 ("Checking", (300, 300, 390, 320)), ("$25.00", (420, 300, 490, 320)),
                 value="$25.00") is None


def test_the_prompt_says_to_save_every_value_a_read_goal_asks_for() -> None:
    text = SRC.read_text()
    prompt = text[text.index("VISUAL_SYSTEM_PROMPT = "):]
    for part in ("MUST save every value the goal asks for with extract_value",
                 "Only saved values reach the caller",
                 "MUST read values BEFORE logging out"):
        assert part in " ".join(prompt[:prompt.index('"""\n', 30)].split())


def test_a_read_with_no_recorded_page_keeps_the_old_rule() -> None:
    """Only text seen on that look can be the checkpoint: an event with no page_texts (an older
    log) proves nothing, so the agent's proof / the model's text is kept."""
    log = _read_log("Accounts Overview")
    del log[1]["page_texts"]
    assert NS["build_capability"](log, _meta(name="r")).checkpoint == "Accounts Overview"


def test_a_two_column_table_with_no_menu_keeps_its_row_key() -> None:
    assert _cell(("Type", (100, 100, 140, 116)), ("Balance", (300, 100, 360, 116)),
                 ("Savings", (100, 126, 165, 142)), ("$25.00", (300, 126, 355, 142)),
                 value="$25.00") == {"row_key": "Savings", "column": "Balance"}

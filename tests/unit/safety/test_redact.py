"""redactor/norm: the value masker discovery uses (numbers however written, whole words)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from cua.safety.redact import NUMBER, norm, redactor

SRC = Path(__file__).parents[3] / "notebooks/discovery/discovery.py"


def _notebook() -> dict[str, object]:
    tree = ast.parse(SRC.read_text())
    names = {"_num", "redactor", "norm"}
    keep = [
        n
        for n in tree.body
        if getattr(n, "name", None) in names
        or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NUMBER")
    ]
    ns: dict[str, object] = {"re": re}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def test_a_number_matches_however_it_is_written() -> None:
    redact = redactor({"100000"})
    assert redact("Balance $100,000.00 today") == "Balance *** today"
    assert redact("100001") == "100001"


def test_words_match_whole_and_case_insensitively() -> None:
    redact = redactor({"IL", "Sean"})
    assert redact("Bill to sean in il") == "Bill to *** in ***"


def test_mask_is_a_parameter() -> None:
    assert redactor({"42"}, mask="[x]")("pay 42") == "pay [x]"


def test_no_values_redacts_nothing() -> None:
    assert redactor(set())("Sean 42") == "Sean 42"


def test_norm_casefolds_squashes_space_and_drops_trailing_punctuation() -> None:
    assert norm("  Zip   Code: ") == "zip code"
    assert norm(None) == ""


def test_parity_with_the_notebook_redactor() -> None:
    ns = _notebook()
    values = {"100000", "IL", "Sean", "$4,242.50", "a"}
    text = "Sean in IL paid $100,000.00 and 4242.5 to Bill; a cat"
    assert redactor(values)(text) == ns["redactor"](values)(text)
    assert redactor(values, mask="#")(text) == ns["redactor"](values, mask="#")(text)
    assert NUMBER.pattern == ns["NUMBER"].pattern
    assert norm(" A b. ") == ns["norm"](" A b. ")

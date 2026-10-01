"""where / label_near / spot / page_texts: a point's label in words, never a value.

Ported from tests/discovery/test_save_artifact.py's ``_look_ns`` tests.
"""

from __future__ import annotations

from cua.discovery.tools.read_helpers import headings, is_word, label_near, page_texts, where
from cua.vision.look import Box, Element, Look


def _look(*els: tuple[int, str, tuple[int, int, int, int]]) -> Look:
    return Look(b"", b"", tuple(Element(r, t, Box(*b)) for r, t, b in els), "u")


def test_where_records_label_box_ordinal_offset_but_not_the_box_contents() -> None:
    look = _look(
        (1, "Amount:", (10, 10, 70, 30)),
        (2, "Amount:", (10, 60, 70, 80)),
        (3, "4242", (100, 60, 160, 80)),
    )
    got = where(look, (130, 70), set())
    assert got["label"] == "Amount:"
    assert got["anchor"]["ordinal"] == 2  # type: ignore[index]  # noqa: PLR2004
    assert got["anchor"]["box"] == [10, 60, 70, 80]
    assert got["offset"] == [90, 0]  # type: ignore[index]
    assert "4242" not in str(got)


def test_a_dropdowns_own_number_is_never_its_label() -> None:
    """Live bug: 'From account #' dropdown showing '74838' was saved as input 'f_74838'."""
    look = _look((1, "From account #:", (10, 60, 120, 80)), (2, "74838", (200, 60, 250, 80)))
    assert where(look, (270, 70), set())["label"] == "From account #:"


def test_a_typed_value_above_is_never_the_next_fields_label() -> None:
    """Live bug: 'Sean' typed into Payee Name became the Address step's label and input name."""
    look = _look(
        (1, "Payee Name:", (10, 10, 110, 30)),
        (2, "Sean", (200, 10, 240, 30)),
        (3, "Address:", (10, 40, 80, 60)),
    )
    assert where(look, (250, 50), set())["label"] == "Address:"  # same row wins
    assert label_near(look, (250, 75), {"sean"}).text == "Address:"  # type: ignore[union-attr]


def test_page_texts_and_headings_are_words_without_run_values() -> None:
    look = _look(
        (1, "Accounts Overview", (0, 0, 200, 40)),
        (2, "16785", (0, 50, 60, 60)),
        (3, "to account 16785", (0, 70, 90, 80)),
        (4, "Balance", (0, 90, 90, 100)),
    )
    assert page_texts(look, {"16785"}) == ["Accounts Overview", "Balance"]
    assert headings(look, {"16785"})[0] == "Accounts Overview"
    assert is_word("Balance", set())
    assert not is_word("16785", set())

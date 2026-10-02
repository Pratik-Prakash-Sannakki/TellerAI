"""IdMask: account ids keep only their last digits, in text, in names and in a PNG; amounts,
timestamps, hashes and short numbers are left alone. url_path / no_session drop the session."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from cua.config import SiteProfile, load_site
from cua.safety.redact import IdMask, mask_png, no_session, redactor, safe_redactor
from cua.vision import Box, decode, encode

IDS = IdMask(min_digits=5, visible=3)


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("from account #98765 to 24680", "from account #***765 to ***680"),
        ("account_98765_transactions", "account_***765_transactions"),
        ("'98765'", "'***765'"),
    ],
)
def test_an_id_keeps_its_last_digits(text: str, want: str) -> None:
    assert IDS(text) == want


@pytest.mark.parametrize(
    "text",
    [
        "$100,000.00 and -$12345 and $12345",  # amounts
        "12,345.67 and 12345.50",  # decimals / thousands
        "20261002T005633Z",  # a timestamp in a folder name
        "claude-sonnet-4-5-20250929",  # a model name
        "564db51bdcdc02242b2391a9e1d1326266e4c8e9",  # a git sha
        "step 1234 at (1280, 800)",  # short numbers, pixels
    ],
)
def test_what_is_not_an_id_is_left_alone(text: str) -> None:
    assert IDS(text) == text


def test_names_keep_the_last_digits_without_stars() -> None:
    assert IDS.name("account_98765_transactions") == "account_765_transactions"
    assert IDS.name("crops/pay_from_98765/s1.png") == "crops/pay_from_765/s1.png"


def test_spans_are_the_hidden_characters() -> None:
    assert IDS.spans("to #98765") == [(4, 6)]


def test_visible_and_min_digits_are_parameters() -> None:
    assert IdMask(min_digits=4, visible=2)("pin 1234") == "pin ***34"


def test_the_site_profile_sets_the_mask() -> None:
    site = load_site("parabank")
    assert IdMask.for_site(site) == IdMask(site.id_min_digits, site.id_visible_digits)
    assert site.id_visible_digits == 3  # noqa: PLR2004
    plain = SiteProfile(name="t", start_url="https://a.test/", allowed_hosts=frozenset({"a.test"}))
    assert (plain.id_min_digits, plain.id_visible_digits) == (5, 3)


def test_ids_keep_last_digits_even_when_they_are_run_values() -> None:
    redact = safe_redactor({"sean", "98765"}, {}, IDS)
    assert redact("pay Sean from 98765") == "pay *** from ***765"


def test_a_digits_only_secret_is_masked_whole_never_by_last_digits() -> None:
    redact = safe_redactor(set(), {"password": "123456"}, IDS)
    assert redact("typed 123456") == "typed ***"


def _png() -> bytes:
    img = np.full((40, 220, 3), 255, np.uint8)
    cv2.putText(img, "#98765", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    return encode(img)


def _ocr(img: object) -> list[tuple[str, Box]]:
    return [("#98765", Box(10, 10, 90, 32)), ("pay Sean", Box(100, 10, 160, 30))]


def test_a_png_run_value_is_still_blacked_out_whole_and_an_id_box_only_in_part() -> None:
    img = decode(mask_png(_png(), safe_redactor({"sean"}, {}, IDS), _ocr, IDS))
    assert img[15:25, 101:159].max() == 0
    assert (img[12:30, 60:90] == 255).any()  # noqa: PLR2004  the id's last digits still show


def test_a_png_secret_shaped_like_an_id_is_blacked_out_whole() -> None:
    img = decode(mask_png(_png(), safe_redactor(set(), {"pin": "98765"}, IDS), _ocr, IDS))
    assert img[10:32, 10:90].max() == 0


def test_without_ids_mask_png_is_unchanged() -> None:
    png = _png()
    assert mask_png(png, redactor({"Nobody"}), _ocr) is png


def test_no_session_drops_the_session_token_and_the_query() -> None:
    url = "https://h.test/app/index.htm;jsessionid=ABC123?id=98765"
    assert no_session(url) == "https://h.test/app/index.htm"
    assert no_session("about:blank") == "about:blank"


def _drawn(text: str, width: int = 400) -> tuple[bytes, Box]:
    """White image, ``text`` drawn in black; the OCR box spans exactly its ink."""
    img = np.full((40, width, 3), 255, np.uint8)
    cv2.putText(img, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cols = np.where((img.min(axis=2) < 128).any(axis=0))[0]  # noqa: PLR2004
    return encode(img), Box(int(cols[0]), 5, int(cols[-1]) + 1, 35)


def _digit_columns(png: bytes, box: Box) -> list[int]:
    """Left x of each glyph in the unmasked drawing (the last 5 are the id's digits)."""
    img = decode(png)[box.y1 : box.y2, box.x1 : box.x2]
    ink = (img.min(axis=2) < 128).any(axis=0).astype(int)  # noqa: PLR2004
    return [box.x1 + int(x) for x in np.where(np.diff(np.concatenate([[0], ink])) == 1)[0]]


@pytest.mark.parametrize("text", ["98765", "From account #: 98765", "#98765"])
def test_a_png_id_shows_exactly_its_last_three_digits(text: str) -> None:
    """Live: 'From account #: 1xxxx' in one OCR box showed 4 digits (the width share is off when
    the label's letters are narrower than digits). The last glyphs are found from the right."""
    png, box = _drawn(text)
    starts = _digit_columns(png, box)
    out = decode(mask_png(png, safe_redactor(set(), {}, IDS), lambda i: [(text, box)], IDS))
    hidden_from, visible_from = starts[-5], starts[-3]
    assert out[8:32, hidden_from:visible_from].max() == 0  # '9', '8' blacked out
    assert (out[:, visible_from:] == decode(png)[:, visible_from:]).all()  # '765' untouched
    assert (out[:, :hidden_from] == decode(png)[:, :hidden_from]).all()  # the label untouched


def test_glyphs_that_cannot_be_told_apart_black_out_the_whole_box() -> None:
    png = encode(np.full((40, 220, 3), 255, np.uint8))  # no ink: no glyphs to count from
    out = decode(
        mask_png(
            png, safe_redactor(set(), {}, IDS), lambda i: [("98765", Box(10, 10, 70, 30))], IDS
        )
    )
    assert out[10:30, 10:70].max() == 0

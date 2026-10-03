"""is_sensitive, hide_secrets, replay's NUMBER variant, mask_png -- each against its notebook."""

from __future__ import annotations

import re
from types import SimpleNamespace

import numpy as np
import pytest

from cua.safety.redact import (
    NUMBER,
    REPLAY_NUMBER,
    hide_secrets,
    is_sensitive,
    mask_png,
    redactor,
)
from cua.vision import Box, decode, encode
from tests.unit.safety._notebook import DISCOVERY, REPLAY, load

WORDS = frozenset({"password", "ssn", "social"})
TEXT = "rung1 paid $100,000.00 to Sean, 4242.5 and 42; v1.42 a42 IL Bill"
VALUES = {"100000", "42", "Sean", "IL", "$4,242.50", "1"}


def test_is_sensitive_is_a_casefolded_substring() -> None:
    assert is_sensitive("Customer SSN", WORDS)
    assert not is_sensitive("Zip", WORDS)


def test_hide_secrets_replaces_each_value_by_its_name() -> None:
    assert hide_secrets("u=bob p=hunter2", {"password": "hunter2", "x": ""}) == "u=bob p=<password>"


@pytest.mark.parametrize("src", [DISCOVERY, REPLAY], ids=["discovery", "replay"])
def test_hide_secrets_parity(src: object) -> None:
    secrets = {"password": "hunter2", "username": "bob"}
    ns = load(src, {"hide_secrets"}, SECRETS=secrets)  # type: ignore[arg-type]
    assert hide_secrets("bob hunter2 x", secrets) == ns["hide_secrets"]("bob hunter2 x")


@pytest.mark.parametrize("src", [DISCOVERY, REPLAY], ids=["discovery", "replay"])
def test_is_sensitive_parity(src: object) -> None:
    ns = load(src, {"is_sensitive"}, CFG=SimpleNamespace(sensitive_words=WORDS))  # type: ignore[arg-type]
    for label in ("Password", "customer.ssn", "Amount", "Social sec"):
        assert is_sensitive(label, WORDS) == ns["is_sensitive"](label)


def test_replay_number_parity() -> None:
    ns = load(REPLAY, {"_num", "redactor"}, frozenset({"NUMBER"}))
    assert REPLAY_NUMBER.pattern == ns["NUMBER"].pattern
    assert redactor(VALUES, number=REPLAY_NUMBER)(TEXT) == ns["redactor"](VALUES)(TEXT)


def test_the_two_numbers_really_differ() -> None:
    assert redactor({"1"})("rung1") == "rung***"
    assert redactor({"1"}, number=REPLAY_NUMBER)("rung1") == "rung1"
    assert NUMBER is not REPLAY_NUMBER


def _png() -> bytes:
    return encode(np.full((40, 120, 3), 255, np.uint8))


def _ocr(img: object) -> list[tuple[str, Box]]:
    return [("pay Sean", Box(10, 10, 60, 30)), ("Total", Box(70, 10, 110, 30))]


def test_mask_png_blacks_out_only_boxes_holding_a_value() -> None:
    img = decode(mask_png(_png(), redactor({"Sean"}), _ocr))
    assert img[15:25, 15:55].max() == 0
    assert img[15:25, 75:105].min() == 255  # noqa: PLR2004


def test_a_value_ocr_reads_without_its_space_is_masked() -> None:
    """Live: value '1 Main' showed unmasked in replay evidence; OCR read the field as '1Main'."""

    def ocr(img: object) -> list[tuple[str, Box]]:
        return [("1Main", Box(10, 10, 60, 30)), ("1 Main", Box(70, 10, 110, 30))]

    img = decode(mask_png(_png(), redactor({"1 Main"}), ocr))
    assert img[15:25, 15:55].max() == 0
    assert img[15:25, 75:105].max() == 0


def test_a_word_value_ignores_spaces_but_stays_whole() -> None:
    redact = redactor({"1 Main"})
    assert redact("at 1Main and 1  Main") == "at *** and ***"
    assert redact("21Main 1Mainly") == "21Main 1Mainly"


def test_a_clean_image_is_returned_as_is() -> None:
    png = _png()
    assert mask_png(png, redactor({"Nobody"}), _ocr) is png


@pytest.mark.parametrize("src", [DISCOVERY, REPLAY], ids=["discovery", "replay"])
def test_mask_png_parity(src: object) -> None:
    ns = load(src, {"mask_png"}, decode=decode, encode=encode, ocr=_ocr)  # type: ignore[arg-type]
    redact = redactor({"Sean"})
    assert mask_png(_png(), redact, _ocr) == ns["mask_png"](_png(), redact)
    assert re  # keep import used by the notebook namespace pattern

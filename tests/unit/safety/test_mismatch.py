"""mismatches/dropdown_options: numbers the human never gave; a dropdown's options, once each."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from cua.safety.mismatch import dropdown_options, mismatches
from tests.unit.safety._notebook import DISCOVERY, REPLAY, load

WORDS = frozenset({"password", "ssn", "social"})
FIELDS = {"amount": "10.00", "fromAccountId": "1450", "ssn": "999", "name": "Ann", "to": "14898"}
STASH = [
    {"value": "14898", "text": "14898", "options": ["14898", "124677"]},
    {"value": "1450", "text": "1450", "options": ["1450", "1400"]},
    {"value": "x", "text": "x", "options": ["x"]},
]


def _hide(text: str) -> str:
    return text.replace("124677", "<secret>")


def test_only_numbers_never_given_are_mismatches() -> None:
    assert mismatches(FIELDS, "transfer $10 to 14898", WORDS) == ["fromAccountId"]


def test_only_the_real_dropdown_becomes_a_dropdown() -> None:
    fields = {"accountId": "14898", "amount": "124677", "address.state": "1", "name": "1"}
    stash = [{"value": "14898", "text": "14898", "options": ["14898", "124677"]}]
    assert dropdown_options(fields, list(fields), stash, lambda t: t) == [
        ["14898", "124677"],
        [],
        [],
        [],
    ]


def test_discovery_parity() -> None:
    goal, given = "transfer $10 to", ["14898"]
    st = SimpleNamespace(goal=goal, given=given, dropdowns=STASH)
    cfg = SimpleNamespace(sensitive_words=WORDS)
    ns = load(
        DISCOVERY,
        {"mismatches", "dropdown_options", "is_sensitive"},
        HANDOFF=st,
        CFG=cfg,
        hide_secrets=_hide,
    )
    text = " ".join([goal, *given])
    assert mismatches(FIELDS, text, WORDS) == ns["mismatches"](FIELDS)
    keys = list(FIELDS)
    old = asyncio.run(ns["dropdown_options"](FIELDS, keys))
    assert dropdown_options(FIELDS, keys, STASH, _hide) == old


def test_replay_parity() -> None:
    given = ["10", "14898"]
    st = SimpleNamespace(given=given, dropdowns=STASH)
    cfg = SimpleNamespace(sensitive_words=WORDS)
    ns = load(
        REPLAY,
        {"mismatches", "dropdown_options", "is_sensitive"},
        STATE=st,
        CFG=cfg,
        hide_secrets=_hide,
    )
    assert mismatches(FIELDS, " ".join(given), WORDS) == ns["mismatches"](FIELDS)
    keys = list(FIELDS)
    assert dropdown_options(FIELDS, keys, STASH, _hide) == ns["dropdown_options"](FIELDS, keys)

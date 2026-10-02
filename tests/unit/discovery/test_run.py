"""DiscoveryRun (was HandoffState): fresh per run, satisfies SendState, wiped after a run."""

from __future__ import annotations

import asyncio

import pytest

from cua.discovery.run import DECLINED, DiscoveryRun, run_values, saved_texts, wipe
from cua.safety import DISCOVERY_OPTIONS, SendState
from cua.vision.look import Look

SECRETS = {"username": "john", "password": "demo"}


def test_given_text_is_the_goal_and_every_answer() -> None:
    run = DiscoveryRun(goal="pay 10", given=["to 14898", "now"])
    assert run.given_text() == "pay 10 to 14898 now"


def test_it_is_a_send_state() -> None:
    state: SendState = DiscoveryRun()
    assert state.allow_send is False
    assert state.takeover is None


def test_declined_is_the_guards_discovery_text() -> None:
    assert DISCOVERY_OPTIONS.decline_text == DECLINED


def test_each_run_has_its_own_counters_and_act_lock() -> None:
    a, b = DiscoveryRun(), DiscoveryRun()
    a.navs += 1
    assert b.navs == 0
    assert isinstance(a.act_lock, asyncio.Lock)
    assert a.act_lock is not b.act_lock


def test_run_values_holds_every_value_and_the_secrets_never_the_mask() -> None:
    run = DiscoveryRun(given=["Jane"], typed_texts={"42"}, entered={"SSN": "******", "Zip": "9021"})
    run.redact = {"16785"}
    assert run_values(run, SECRETS) == {"jane", "42", "9021", "16785", "john", "demo"}


def test_saved_texts_includes_table_cells() -> None:
    assert saved_texts({"a": "1", "t": [{"x": "2", "y": ""}]}) == {"1", "2"}


@pytest.mark.parametrize("with_table", [False, True])
def test_after_wipe_the_run_holds_no_given_text_entered_values_or_look(with_table: bool) -> None:
    """Review focus 5: values live only for the run (banking). The log keeps labels only."""
    run = DiscoveryRun(goal="pay $10 to Jane", given=["Jane"], typed_texts={"42"})
    run.entered = {"Amount": "42"}
    run.look = Look(b"", b"", (), "u")
    run.saved = {"t": [{"Name": "Jane Doe"}]} if with_table else {"balance": "$99.00"}
    run.log = [
        {
            "tool": "type_text",
            "args": {},
            "result": "ok",
            "point": None,
            "url": "u",
            "crop": None,
            "label": "to Jane",
        },
    ]
    wipe(run, SECRETS)
    assert run.given == []
    assert run.entered == {}
    assert run.look is None
    assert run.typed_texts == set()
    assert run.log[0].get("leak") is True  # flagged before the values were dropped
    assert {"jane", "42", "john"} <= run.redact
    assert ("Jane Doe" if with_table else "$99.00") in run.redact


def test_saved_texts_includes_saved_options() -> None:
    assert saved_texts({"accounts": ["***010", "14232"]}) == {"***010", "14232"}

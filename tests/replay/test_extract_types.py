"""Replay's own strict value types for extracts: an account number is never a currency."""
import asyncio

import pytest

ROWS = [("Account", (10, 10, 80, 30)), ("Balance", (200, 10, 270, 30)),
        ("13566", (10, 50, 60, 70)), ("$515.50", (200, 50, 260, 70))]


@pytest.mark.parametrize("text", ["-$202,484.50", "$0.00", "1,234.56", "$515", "$-10.00", " $1,000.00 "])
def test_currency_needs_a_dollar_or_two_decimals(ns, text) -> None:
    assert ns["is_type"](text, "currency")


@pytest.mark.parametrize("text", ["13566", "1,234", "12.5", "$", "abc", "", "13566.123"])
def test_an_integer_or_id_is_not_currency(ns, text) -> None:
    assert not ns["is_type"](text, "currency")


def test_other_types_unchanged(ns) -> None:
    t = ns["is_type"]
    assert t("13566", "integer") and not t("1.5", "integer")
    assert t("1.5", "number") and t("hello", "string") and t("Yes", "boolean")
    assert not t("x", "unknown-type")


def _cap(ns, target, kind="currency"):
    step = ns["SCHEMA"]["Extract"](save_as="first_balance", target=target)
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=[step], checkpoint="Balance",
                            outputs=[{"name": "first_balance", "type": kind, "description": "b"}])


def _extract(ns, mk_look, cap):
    ns["STATE"].look = mk_look(ROWS)
    step = cap.steps[0]
    hit = ns["locate"](ns["STATE"].look, step.target, {}, None)
    ns["STATE"].rung = hit[1]                                  # what run_step sets before the action
    return asyncio.run(ns["do_extract"](step, hit[0], cap))


def test_an_account_number_cell_for_a_currency_output_stops(ns, mk_look) -> None:
    cap = _cap(ns, {"table_cell": {"row_key": "13566", "column": "Account"},
                    "anchor": {"label": "Account", "offset": [0, 40]}})
    with pytest.raises(ns["Stop"]) as e:
        _extract(ns, mk_look, cap)
    assert e.value.status == "STUCK" and e.value.expected == "currency" and e.value.observed == "13566"
    assert "first_balance" not in ns["STATE"].outputs


def test_the_next_rung_is_tried_once_on_a_type_mismatch(ns, mk_look) -> None:
    cap = _cap(ns, {"table_cell": {"row_key": "13566", "column": "Account"},     # wrong cell
                    "anchor": {"label": "Balance", "offset": [-5, 40]}})          # right cell
    assert _extract(ns, mk_look, cap) is True
    assert ns["STATE"].outputs["first_balance"] == "$515.50" and ns["STATE"].rung == "rung2"


def test_the_observed_text_is_masked(ns, mk_look) -> None:
    ns["SECRETS"]["username"] = "13566"
    cap = _cap(ns, {"table_cell": {"row_key": "Account", "column": "Account"},
                    "anchor": {"label": "Account", "offset": [0, 40]}})
    with pytest.raises(ns["Stop"]) as e:
        _extract(ns, mk_look, cap)
    assert "13566" not in e.value.observed


def test_the_walk_does_not_return_success(ns, mk_look) -> None:
    lk = mk_look(ROWS)

    async def take_look():
        ns["STATE"].look = lk
        return lk

    ns.update(take_look=take_look, CFG=ns["Config"](check_s=0))
    ns["STATE"].look = lk
    cap = _cap(ns, {"table_cell": {"row_key": "13566", "column": "Account"},
                    "anchor": {"label": "Account", "offset": [0, 40]}})
    with pytest.raises(ns["Stop"]) as e:
        asyncio.run(ns["walk"](cap, None, []))
    assert e.value.status == "STUCK"

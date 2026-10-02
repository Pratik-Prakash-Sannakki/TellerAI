"""Typed inputs: the recorder infers each input's type from the shapes of the values typed into
it (logged as shapes, never as values). One shape for every value -> that type, else string."""

from __future__ import annotations

import yaml

from cua.discovery.recorder import build_capability, save_artifact, shapes_of
from cua.discovery.recorder.types import PRECEDENCE, pick_type
from tests.unit.discovery.recorder.test_recorder import LOGIN, REF, SENT, START, _ev, _meta


def _typed(label: str, value: str) -> dict:
    return _ev("type_text", REF, "Typed at (300, 200).", label=label, shapes=shapes_of(value))


def _types(*events: dict) -> dict[str, str]:
    cap = build_capability([START, *events, SENT], _meta(name="pay"))
    return {i.name: i.type for i in cap.inputs}


def test_shapes_of_lists_every_matching_shape_in_precedence_order() -> None:
    assert shapes_of("100") == ["number", "integer", "id"]
    assert shapes_of("123.45") == ["currency", "number"]
    assert shapes_of("2026-01-01") == ["date", "id"]
    assert shapes_of("hello there") == []


def test_precedence_is_documented_and_covers_the_shapes() -> None:
    assert PRECEDENCE == ("email", "phone", "date", "currency", "number", "integer", "id")


def test_all_currency_values_make_a_currency_input() -> None:
    assert _types(_typed("Amount", "123.45"), _typed("Amount", "$9.99")) == {"amount": "currency"}


def test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later() -> None:
    assert _types(_typed("Amount", "100")) == {"amount": "number"}


def test_mixed_shapes_fall_back_to_their_common_type() -> None:
    assert pick_type([["currency", "number"], ["number", "integer", "id"]]) == "number"


def test_values_with_no_shape_in_common_are_string() -> None:
    assert _types(_typed("Memo", "2026-01-01"), _typed("Memo", "a@b.co")) == {"memo": "string"}


def test_a_value_with_no_shape_is_string() -> None:
    assert _types(_typed("Payee Name", "Jane Doe")) == {"payee_name": "string"}


def test_an_event_without_shapes_is_string() -> None:
    """Older logs (and any tool that did not log shapes) never guess a type."""
    assert _types(_ev("type_text", REF, "Typed at (300, 200).", label="Amount")) == {
        "amount": "string"
    }


def _entry(label: str, value: str) -> dict:
    return _ev(
        "request_value",
        {"hint": label},
        "human entry",
        label=label,
        human_entry=True,
        dropdown=False,
        shapes=shapes_of(value),
    )


def test_a_digit_only_human_entry_does_not_make_a_number_input() -> None:
    """Bug: a human typed fake digits ("1") into City during discovery and City became a number
    input, so replay refused "Springfield". A human's discovery answer is placeholder data: digits
    alone cannot tell a text box from a number box."""
    assert _types(_entry("City:", "1"), _entry("Zip Code:", "90210")) == {
        "city": "string",
        "zip_code": "string",
    }


def test_a_human_entry_still_types_by_a_structural_shape() -> None:
    assert _types(
        _entry("Email:", "jane@example.com"),
        _entry("Phone #:", "555-123-4567"),
        _entry("Date:", "2026-01-01"),
        _entry("Amount:", "12.50"),
    ) == {"email": "email", "phone": "phone", "date": "date", "amount": "currency"}


def test_a_goal_value_the_agent_types_still_makes_a_number_input() -> None:
    assert _types(_typed("Account #", "12345")) == {"account": "number"}


def test_open_path_query_value_is_typed_from_its_shape() -> None:
    nav = _ev("open_path", {"path": "activity.htm?id=12345"}, "Opened activity.htm?id=12345.")
    assert _types(nav) == {"id": "number"}


def test_a_secret_is_never_an_input_and_never_typed() -> None:
    cap = build_capability([*LOGIN, SENT], _meta())
    assert cap.inputs == []
    assert cap.secrets == ["username", "password"]


def test_no_typed_value_reaches_the_capability_or_its_yaml(tmp_path) -> None:  # noqa: ANN001
    value = "4321.99"
    cap = build_capability([START, _typed("Amount", value), SENT], _meta(name="pay"))
    assert cap.inputs[0].type == "currency"
    assert value not in cap.model_dump_json()
    text = save_artifact(cap, {}, tmp_path).read_text()
    assert value not in text
    assert yaml.safe_load(text)["inputs"][0] == {
        "name": "amount",
        "type": "currency",
        "description": "amount",
    }

"""sent_fields/rebuilt/pretty: what a request sends, and the same request with edited values."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from cua.safety.request import _flat, _json, pretty, rebuilt, sent_fields
from tests.unit.safety._notebook import DISCOVERY, REPLAY, load

NAMES = {"_flat", "_json", "sent_fields", "rebuilt", "pretty"}
JSON_BODY = json.dumps({"name": "Acme", "address": {"zipCode": "12180"}, "n": 777, "tags": [1]})
REQS = [
    SimpleNamespace(url="https://x/t?accountId=1&amount=2", method="POST", post_data=JSON_BODY),
    SimpleNamespace(url="https://x/t", method="POST", post_data="amount=10&fromAccountId=14898"),
    SimpleNamespace(url="https://x/t?a=1", method="POST", post_data=None),
    SimpleNamespace(url="https://x/t", method="POST", post_data="[1, 2]"),
]
EDITS = {"amount": "25", "name": "Acme Power", "n": "778", "accountId": "9", "a": "3"}


def test_json_body_is_flattened_with_dotted_keys_and_lists_dropped() -> None:
    assert sent_fields(REQS[0]) == {
        "accountId": "1",
        "amount": "2",
        "name": "Acme",
        "address.zipCode": "12180",
        "n": "777",
    }


def test_rebuilt_json_keeps_numbers_numbers() -> None:
    url, body = rebuilt(REQS[0], {**sent_fields(REQS[0]), **EDITS})
    assert url == "https://x/t?accountId=9&amount=25"
    assert json.loads(body or "")["n"] == 778  # noqa: PLR2004


def test_flat_and_json_helpers() -> None:
    assert _flat({"a": {"b": None}}) == {"a.b": ""}
    assert _json("[1]") is None
    assert _json("nope") is None


def test_pretty() -> None:
    assert pretty("address.zipCode") == "Address zip code"


@pytest.mark.parametrize("src", [DISCOVERY, REPLAY], ids=["discovery", "replay"])
@pytest.mark.parametrize("req", REQS)
def test_parity_with_each_notebook(src: object, req: SimpleNamespace) -> None:
    ns = load(src, NAMES)  # type: ignore[arg-type]
    assert sent_fields(req) == ns["sent_fields"](req)
    fields = {**sent_fields(req), **{k: v for k, v in EDITS.items() if k in sent_fields(req)}}
    assert rebuilt(req, fields) == ns["rebuilt"](req, fields)
    assert pretty("customer.firstName_x") == ns["pretty"]("customer.firstName_x")

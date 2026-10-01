"""Extract steps on fakes: strict value types and an optional `pattern`. Ported from
tests/replay/test_extract_types.py and test_extract_pattern.py."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cua.config import ReplayConfig
from cua.replay import engine, steps
from cua.replay.context import Ctx
from cua.replay.locate import locate
from cua.schema import TYPES, Capability, Stop
from tests.unit._snapshots import DISCOVERY as SNAP_DISCOVERY
from tests.unit._snapshots import REPLAY as SNAP_REPLAY
from tests.unit.replay.helpers import (
    cap,
    extract,
    make_replay_ctx,
    mk_look,
    screen,
)

# --- extract types (test_extract_types.py) -------------------------------------------------

TROWS = [
    ("Account", (10, 10, 80, 30)),
    ("Balance", (200, 10, 270, 30)),
    ("13566", (10, 50, 60, 70)),
    ("$515.50", (200, 50, 260, 70)),
]


@pytest.mark.parametrize(
    "text", ["-$202,484.50", "$0.00", "1,234.56", "$515", "$-10.00", " $1,000.00 "]
)
def test_currency_needs_a_dollar_or_two_decimals(text: str) -> None:
    assert steps.is_type(text, "currency")


@pytest.mark.parametrize("text", ["13566", "1,234", "12.5", "$", "abc", "", "13566.123"])
def test_an_integer_or_id_is_not_currency(text: str) -> None:
    assert not steps.is_type(text, "currency")


def test_other_types_unchanged() -> None:
    t = steps.is_type
    assert t("13566", "integer") and not t("1.5", "integer")
    assert t("1.5", "number") and t("hello", "string") and t("Yes", "boolean")
    assert not t("x", "unknown-type")


def _xcap(
    target: dict[str, object], kind: str = "currency", name: str = "first_balance", **kw: object
) -> Capability:
    return cap(
        [extract(name, target, **kw)],
        "Balance",
        outputs=[{"name": name, "type": kind, "description": "b"}],
    )


async def _extract(
    ctx: Ctx, cp: Capability, rows: list[tuple[str, tuple[int, int, int, int]]]
) -> bool:
    ctx.run.look = mk_look(rows)
    step = cp.steps[0]
    hit = locate(ctx.run.look, step.target, {}, None, ctx.cfg)  # type: ignore[union-attr]
    assert hit is not None
    ctx.run.rung = hit[1]  # what run_step sets before the action
    return await steps.do_extract(ctx, step, hit[0], cp)


WRONG = {"table_cell": {"row_key": "13566", "column": "Account"}}


@pytest.mark.asyncio
async def test_an_account_number_cell_for_a_currency_output_stops() -> None:
    ctx = make_replay_ctx()
    cp = _xcap({**WRONG, "anchor": {"label": "Account", "offset": [0, 40]}})
    with pytest.raises(Stop) as e:
        await _extract(ctx, cp, TROWS)
    assert (
        e.value.status == "STUCK" and e.value.expected == "currency" and e.value.observed == "13566"
    )
    assert "first_balance" not in ctx.run.outputs


@pytest.mark.asyncio
async def test_the_next_rung_is_tried_once_on_a_type_mismatch() -> None:
    ctx = make_replay_ctx()
    cp = _xcap({**WRONG, "anchor": {"label": "Balance", "offset": [-5, 40]}})
    assert await _extract(ctx, cp, TROWS) is True
    assert ctx.run.outputs["first_balance"] == "$515.50" and ctx.run.rung == "rung2"


@pytest.mark.asyncio
async def test_the_observed_text_is_masked() -> None:
    ctx = make_replay_ctx()
    ctx.secrets = {"username": "13566"}
    cp = _xcap(
        {
            "table_cell": {"row_key": "Account", "column": "Account"},
            "anchor": {"label": "Account", "offset": [0, 40]},
        }
    )
    with pytest.raises(Stop) as e:
        await _extract(ctx, cp, TROWS)
    assert "13566" not in e.value.observed


@pytest.mark.asyncio
async def test_the_walk_does_not_return_success() -> None:
    ctx = make_replay_ctx(cfg=ReplayConfig(check_s=0))
    screen(ctx, mk_look(TROWS))
    cp = _xcap({**WRONG, "anchor": {"label": "Account", "offset": [0, 40]}})
    with pytest.raises(Stop) as e:
        await engine.walk(ctx, cp, None, [])
    assert e.value.status == "STUCK"


# --- extract pattern (test_extract_pattern.py) ---------------------------------------------

SENTENCE = "www.parasoft.com or call 888-305-0041"
PROWS = [("Contact", (10, 10, 80, 30)), (SENTENCE, (100, 10, 400, 30))]


def _pcap(kind: str, pattern: str | None = None, label: str = "Contact") -> Capability:
    extra = {"pattern": pattern} if pattern else {}
    return _xcap({"anchor": {"label": label, "offset": [200, 0]}}, kind, "v", **extra)


@pytest.mark.asyncio
async def test_a_pattern_extracts_the_phone_from_the_sentence() -> None:
    ctx = make_replay_ctx()
    assert await _extract(ctx, _pcap("phone", TYPES["phone"]), PROWS) is True
    assert ctx.run.outputs["v"] == "888-305-0041"


@pytest.mark.asyncio
async def test_no_match_fails_the_step() -> None:
    ctx = make_replay_ctx()
    with pytest.raises(Stop) as e:
        await _extract(ctx, _pcap("email", TYPES["email"]), PROWS)
    assert e.value.status == "STUCK" and e.value.expected == "email" and "v" not in ctx.run.outputs


@pytest.mark.asyncio
async def test_a_no_match_tries_the_next_rung_first() -> None:
    rows = [
        ("Contact", (10, 10, 80, 30)),
        ("no phone here", (100, 10, 400, 30)),
        ("Call", (10, 60, 60, 80)),
        (SENTENCE, (100, 60, 400, 80)),
    ]
    target = {
        "table_cell": {"row_key": "Contact", "column": "Contact"},
        "anchor": {"label": "Call", "offset": [200, 0]},
    }
    cp = _xcap(target, "phone", "v", pattern=TYPES["phone"])
    ctx = make_replay_ctx(look=mk_look(rows))
    ctx.run.rung = "table"
    assert await steps.do_extract(ctx, cp.steps[0], (250, 20), cp) is True
    assert ctx.run.outputs["v"] == "888-305-0041" and ctx.run.rung == "rung2"


@pytest.mark.parametrize(
    ("kind", "good", "bad"),
    [
        (
            "phone",
            ["888-305-0041", "(888) 305-0041", "+888.305.0041"],
            ["305-0041", "13566", "phone"],
        ),
        ("email", ["a.b+c@x-y.co.uk"], ["a@b", "@x.com", "x.com"]),
        ("date", ["09/30/2026", "2026-09-30", "30.9.26"], ["2026", "Sept 30"]),
        ("id", ["13566", "AB123-X", "x9_y"], ["abc", "-1", ""]),
        ("currency", ["$0.00", "1,234.56"], ["13566"]),
    ],
)
def test_new_types_accept_and_reject(kind: str, good: list[str], bad: list[str]) -> None:
    assert all(steps.is_type(g, kind) for g in good), kind
    assert not any(steps.is_type(b, kind) for b in bad), kind


def _notebook_assign(name: str, notebook: Path) -> object:
    src = notebook.read_text()
    node = next(
        n
        for n in ast.parse(src).body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name
    )
    return ast.literal_eval(node.value)


def test_shapes_are_identical_to_both_notebooks() -> None:
    for nb in (SNAP_DISCOVERY, SNAP_REPLAY):
        shapes = _notebook_assign("SHAPES", nb)
        assert {k: TYPES[k] for k in shapes} == shapes  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_an_old_artifact_without_a_pattern_is_unchanged() -> None:
    rows = [("Balance", (10, 10, 80, 30)), ("$515.50", (230, 10, 290, 30))]
    cp = _pcap("currency", label="Balance")
    assert cp.steps[0].pattern is None  # type: ignore[union-attr]
    ctx = make_replay_ctx()
    assert await _extract(ctx, cp, rows) is True and ctx.run.outputs["v"] == "$515.50"
    with pytest.raises(Stop):
        await _extract(ctx, _pcap("phone"), PROWS)

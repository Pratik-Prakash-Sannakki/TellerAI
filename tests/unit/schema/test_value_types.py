"""cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cua.schema import SHAPES, TYPES, value_matches_type

ROOT = Path(__file__).parents[3]
NOTEBOOKS = [ROOT / "notebooks/discovery/discovery.py", ROOT / "notebooks/replay/replay.py"]


def _tables(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec both)."""
    keep = [
        n
        for n in ast.parse(path.read_text()).body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("SHAPES", "TYPES")
    ]
    ns: dict[str, dict[str, str]] = {}
    exec(compile(ast.Module(keep, []), str(path), "exec"), ns)
    return ns["SHAPES"], ns["TYPES"]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_tables_equal_the_notebooks(path: Path) -> None:
    shapes, types = _tables(path)
    assert shapes == SHAPES
    assert types == TYPES


@pytest.mark.parametrize(
    ("value", "kind", "ok"),
    [
        ("888-305-0041", "phone", True),
        ("$1,234.56", "currency", True),
        ("abc", "number", False),
        ("Yes", "boolean", True),
        ("x", "no_such_type", False),
    ],
)
def test_value_matches_type(value: str, kind: str, ok: bool) -> None:
    assert value_matches_type(value, kind) is ok

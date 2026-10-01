"""The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from every module's AST.

- ``cua.schema``, ``cua.vision``: nothing else from cua besides ``cua.config`` (step-10 brief;
  ``vision/screenshot.py`` and ``vision/crops.py`` use ``BrowserConfig``; schema uses none).
- ``cua.browser``: only ``cua.vision`` / ``cua.config``.
- ``cua.safety``, ``cua.handoff``: only ``cua.schema`` / ``vision`` / ``browser`` / ``config``.
- ``cua.discovery`` never imports ``cua.replay``, and replay never imports discovery.
Every layer may import itself. TYPE_CHECKING-only imports count too.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parents[2] / "src"
ALLOWED = {
    "schema": {"schema", "config"},
    "vision": {"vision", "config"},
    "browser": {"browser", "vision", "config"},
    "safety": {"safety", "schema", "vision", "browser", "config"},
    "handoff": {"handoff", "schema", "vision", "browser", "config"},
}
NEVER = {"discovery": "replay", "replay": "discovery"}


def _module(path: Path) -> str:
    return ".".join(path.relative_to(SRC).with_suffix("").parts).removesuffix(".__init__")


def _cua_imports(path: Path, module: str | None = None) -> set[str]:
    """The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)."""
    out: set[str] = set()
    package = (module or _module(path)).split(".")
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level] if node.level else []
            mod = ".".join([*base, node.module or ""]).strip(".")
            names = [mod] if node.module else [f"{mod}.{a.name}" for a in node.names]
        else:
            continue
        out |= {n.split(".")[1] for n in names if n.startswith("cua.") and n.count(".") >= 1}
    return out


def _layer_files(layer: str) -> list[Path]:
    return sorted((SRC / "cua" / layer).rglob("*.py"))


def test_every_layer_exists() -> None:
    assert all(_layer_files(layer) for layer in [*ALLOWED, *NEVER])


@pytest.mark.parametrize("layer", list(ALLOWED))
def test_a_lower_layer_imports_only_what_it_may(layer: str) -> None:
    bad = {
        str(p.relative_to(SRC)): sorted(extra)
        for p in _layer_files(layer)
        if (extra := _cua_imports(p) - ALLOWED[layer])
    }
    assert bad == {}


def test_schema_imports_no_other_cua_module_at_all() -> None:
    assert {
        str(p.relative_to(SRC)): _cua_imports(p) - {"schema"} for p in _layer_files("schema")
    } == {str(p.relative_to(SRC)): set() for p in _layer_files("schema")}


@pytest.mark.parametrize(("layer", "other"), list(NEVER.items()))
def test_discovery_and_replay_never_import_each_other(layer: str, other: str) -> None:
    bad = [str(p.relative_to(SRC)) for p in _layer_files(layer) if other in _cua_imports(p)]
    assert bad == []


def test_the_checker_sees_absolute_and_relative_imports(tmp_path: Path) -> None:
    """Guard the guard: a planted forbidden import is caught in both spellings."""
    probe = tmp_path / "probe.py"
    probe.write_text("import cua.replay.engine\nfrom ..discovery import goal\nfrom . import look\n")
    assert _cua_imports(probe, "cua.schema.probe") == {"replay", "discovery", "schema"}

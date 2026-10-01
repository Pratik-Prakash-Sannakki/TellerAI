"""The two notebooks are thin demos over the package (step 10). Offline checks only: the jupytext
pair, the cell markers, the OFFLINE (import) cell executed for real, every name a BROWSER cell uses
defined, and every package call bound against the real signature. No BROWSER cell ever runs here.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import jupytext
import pytest

ROOT = Path(__file__).parents[2]
NOTEBOOKS = [ROOT / "notebooks/discovery/discovery.py", ROOT / "notebooks/replay/replay.py"]
MIN_CODE_CELLS, MAX_CODE_CELLS = 3, 6
TITLES = {
    "discovery": ["# Visual discovery", "## Setup", "## Run", "## Save artifact", "## Evidence"],
    "replay": ["# Visual replay", "## Setup", "## Run", "## Evidence"],
}


def _code_cells(path: Path) -> list[str]:
    nb = jupytext.read(path)
    return [c.source for c in nb.cells if c.cell_type == "code"]


def _markdown(path: Path) -> str:
    return "\n".join(c.source for c in jupytext.read(path).cells if c.cell_type == "markdown")


def _tree(src: str) -> ast.Module:
    return compile(src, "<cell>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT | ast.PyCF_ONLY_AST)


def _offline_namespace(path: Path) -> dict[str, object]:
    ns: dict[str, object] = {}
    for src in _code_cells(path):
        if src.startswith("# OFFLINE"):
            exec(compile(src, str(path), "exec"), ns)  # noqa: S102 (imports + load_site only)
    return ns


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_the_py_parses_with_top_level_await(path: Path) -> None:
    compile(path.read_text(), str(path), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_it_is_a_thin_demo_with_marked_cells(path: Path) -> None:
    cells = _code_cells(path)
    assert MIN_CODE_CELLS <= len(cells) <= MAX_CODE_CELLS
    assert all(c.startswith(("# OFFLINE", "# BROWSER")) for c in cells)
    assert cells[0].startswith("# OFFLINE")
    assert len(path.read_text().splitlines()) < 120  # noqa: PLR2004


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_it_keeps_its_markdown_titles(path: Path) -> None:
    md = _markdown(path)
    assert all(t in md for t in TITLES[path.stem])


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_the_ipynb_pair_is_in_sync_and_stripped(path: Path) -> None:
    ipynb = path.with_suffix(".ipynb")
    raw = json.loads(ipynb.read_text())
    assert raw["metadata"]["kernelspec"] == {
        "display_name": "BankerAgent (.venv)",
        "language": "python",
        "name": "banker-agent",
    }
    assert all(not c.get("outputs") for c in raw["cells"])
    assert all(c.get("execution_count") is None for c in raw["cells"] if c["cell_type"] == "code")
    assert [c.source for c in jupytext.read(ipynb).cells] == [
        c.source for c in jupytext.read(path).cells
    ]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_every_name_a_cell_uses_is_defined(path: Path) -> None:
    ns = _offline_namespace(path)
    assigned: set[str] = set()
    used: set[str] = set()
    for src in _code_cells(path):
        for node in ast.walk(_tree(src)):
            if isinstance(node, ast.Name):
                (used if isinstance(node.ctx, ast.Load) else assigned).add(node.id)
            elif isinstance(node, ast.comprehension | ast.arg):
                pass
    assert used - assigned - set(ns) - set(dir(builtins)) == set()


def _bind(fn: object, call: ast.Call) -> None:
    sig = inspect.signature(fn)  # type: ignore[arg-type]
    args = [None] * len(call.args)
    kwargs = {k.arg: None for k in call.keywords if k.arg}
    sig.bind(*args, **kwargs)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_every_package_call_matches_its_signature(path: Path) -> None:
    ns = _offline_namespace(path)
    checked = 0
    for src in _code_cells(path):
        for node in ast.walk(_tree(src)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                fn = ns.get(node.func.id)
                if getattr(fn, "__module__", "").startswith("cua"):
                    _bind(fn, node)
                    checked += 1
    assert checked >= 4  # noqa: PLR2004


def test_the_replay_demo_runs_a_saved_artifact() -> None:
    src = NOTEBOOKS[1].read_text()
    assert '"get_all_account_balances.yaml"' in src
    assert (ROOT / "artifacts/get_all_account_balances.yaml").is_file()

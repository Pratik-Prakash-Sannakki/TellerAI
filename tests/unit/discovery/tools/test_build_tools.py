"""build_tools(ctx): the notebook's 12 tools, in its TOOLS order, with its names, signatures and
docstrings (the model reads them, so they are behaviour)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from cua.discovery.tools import build_tools
from cua.discovery.wiring import new_run
from tests.fakes import make_ctx

SRC = Path(__file__).parents[4] / "notebooks/discovery/discovery.py"
TREE = ast.parse(SRC.read_text())
NAMES = [
    "observe",
    "click",
    "type_text",
    "type_secret",
    "select_option",
    "scroll",
    "open_path",
    "extract_value",
    "extract_table",
    "finish_business_outcome",
    "request_missing_values",
    "ask_human",
]


def _notebook_tools() -> dict[str, ast.AsyncFunctionDef]:
    return {n.name: n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef) and n.name in NAMES}


def _params(node: ast.AsyncFunctionDef) -> list[tuple[str, str, object]]:
    args = node.args.args
    defaults = [None] * (len(args) - len(node.args.defaults)) + [
        ast.literal_eval(d) for d in node.args.defaults
    ]
    return [
        (a.arg, ast.unparse(a.annotation) if a.annotation else "", d)
        for a, d in zip(args, defaults, strict=True)
    ]


def test_the_notebooks_tools_list_is_the_one_we_build() -> None:
    tools = next(
        n
        for n in TREE.body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TOOLS"
    )
    assert [e.id for e in tools.value.elts] == NAMES  # type: ignore[attr-defined]


def test_build_tools_returns_the_twelve_tools_in_order() -> None:
    assert [t.name for t in build_tools(make_ctx())] == NAMES


def test_each_docstring_is_the_notebooks() -> None:
    nb = _notebook_tools()
    for t in build_tools(make_ctx()):
        want = inspect.cleandoc(ast.get_docstring(nb[t.name], clean=False) or "")
        assert inspect.cleandoc(t.coroutine.__doc__ or "") == want, t.name  # type: ignore[attr-defined]


def test_each_signature_is_the_notebooks() -> None:
    nb = _notebook_tools()
    for t in build_tools(make_ctx()):
        sig = inspect.signature(t.coroutine)  # type: ignore[arg-type]
        got = [
            (
                p.name,
                str(p.annotation) if p.annotation is not p.empty else "",
                None if p.default is p.empty else p.default,
            )
            for p in sig.parameters.values()
        ]
        assert got == _params(nb[t.name]), t.name


def test_the_model_sees_each_args_description() -> None:
    by_name = {t.name: t for t in build_tools(make_ctx())}
    assert by_name["click"].args["ref"]["description"] == "Number of the box in the latest look."
    assert (
        "x,y of the box itself" in by_name["request_missing_values"].args["fields"]["description"]
    )
    assert by_name["observe"].args == {}


@pytest.mark.asyncio
async def test_tools_built_once_see_the_run_swapped_in_later() -> None:
    ctx = make_ctx(goal="first")
    finish = build_tools(ctx)[NAMES.index("finish_business_outcome")]
    new_run(ctx, "second")
    out = await finish.ainvoke({"outcome": "x", "proof_text": "nothing"})
    assert out.startswith("REFUSED")
    assert ctx.run.goal == "second"
    assert ctx.run.steps == 1

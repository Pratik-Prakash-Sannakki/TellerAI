"""Load replay.py's definitions via ast (no browser, no OCR model), as tests/discovery does."""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parents[2] / "notebooks/replay/replay.py"
SKIP = {"OCR_ENGINE", "LOCK", "CONTROL", "result"}


def _keep(node: ast.stmt) -> bool:
    if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return True
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return not {getattr(t, "id", "") for t in targets} & SKIP
    return False


@pytest.fixture
def ns() -> dict:
    tree = ast.parse(SRC.read_text())
    body = [n for n in tree.body if _keep(n)]
    out: dict = {}
    exec(compile(ast.Module(body, []), str(SRC), "exec"), out)
    out["EXT"] = None                        # no hand-back extension unless a test adds one
    out["SECRETS"].clear()
    out["SECRETS"].update({"username": "u-secret", "password": "p-secret"})
    return out


@pytest.fixture
def mk_look(ns: dict):
    """mk_look([(text, (x1, y1, x2, y2)), ...]) -> a Look with those OCR elements."""
    def make(items, png: bytes = b"", url: str = "https://parabank.parasoft.com/parabank/x.htm"):
        els = tuple(ns["Element"](i + 1, t, ns["Box"](*b)) for i, (t, b) in enumerate(items))
        return ns["Look"](png, png, els, url)
    return make

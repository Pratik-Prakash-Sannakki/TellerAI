"""Exec chosen top-level defs of a notebook (the old ast-exec pattern) for parity tests."""

from __future__ import annotations

import ast
import functools
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

ROOT = Path(__file__).parents[3]
DISCOVERY = ROOT / "notebooks/discovery/discovery.py"
REPLAY = ROOT / "notebooks/replay/replay.py"
BASE = {
    "re": re,
    "json": json,
    "functools": functools,
    "urlparse": urlparse,
    "parse_qsl": parse_qsl,
    "urlencode": urlencode,
}


def load(src: Path, names: set[str], assigns: frozenset[str] = frozenset(), **ns: object) -> dict:
    tree = ast.parse(src.read_text())
    keep = [
        n
        for n in tree.body
        if getattr(n, "name", None) in names
        or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in assigns)
    ]
    env: dict = {**BASE, **ns}
    exec(compile(ast.Module(keep, []), str(src), "exec"), env)
    return env

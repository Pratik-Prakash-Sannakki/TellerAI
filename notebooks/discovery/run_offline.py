"""Run ONLY the `# %% OFFLINE` cells of one or more jupytext files, in order, in one namespace (Q-D).

Usage (from the repo root, with any Python that has the `discovery` dependency group installed):
    python notebooks/discovery/run_offline.py                      # runs discovery.py
    python notebooks/discovery/run_offline.py parts/p0.py parts/p1.py

Never runs a BROWSER cell (or a markdown cell). Before any cell runs it:
- removes API keys, tokens, secrets and ParaBank credentials from os.environ,
- turns `dotenv.load_dotenv` / `dotenv.main.load_dotenv` into no-ops and `dotenv_values` into `{}`
  (cua.config calls `load_dotenv(override=True)` on import, which would re-load .env),
- refuses to start if a `cua` module was already imported (it would hold values read earlier),
- blocks every `playwright` import, direct or indirect (a sys.meta_path hook, not just a regex).
After the run it re-checks that no secret is in os.environ and playwright is not in sys.modules.
Stops at the first failing cell (non-zero exit).
"""

from __future__ import annotations

import importlib.abc
import os
import pathlib
import re
import sys
import time
import traceback
import types
from collections.abc import Sequence
from importlib.machinery import ModuleSpec

SCRUB = ("ANTHROPIC_API_KEY", "TYPESAFE_API_KEY", "OPENAI_API_KEY", "PARABANK_USERNAME", "PARABANK_PASSWORD")
SECRET_NAME_RE = re.compile(r"(API_KEY|TOKEN|SECRET|PASSWORD)$|^PARABANK_")
CELL_RE = re.compile(r"^# %%(.*)$", re.MULTILINE)
OFFLINE_RE = re.compile(r"^OFFLINE\b")
PLAYWRIGHT_RE = re.compile(r"^\s*(import|from)\s+playwright", re.MULTILINE)


class PlaywrightBlocker(importlib.abc.MetaPathFinder):
    """Refuse any `playwright` import while OFFLINE cells run, however indirect."""

    def find_spec(
        self, fullname: str, path: Sequence[str] | None, target: types.ModuleType | None = None
    ) -> ModuleSpec | None:
        if fullname == "playwright" or fullname.startswith("playwright."):
            raise ImportError(f"OFFLINE run: import of {fullname!r} is blocked")
        return None


def split_cells(source: str) -> list[tuple[str, str]]:
    """(header, body) for every `# %%` cell in a jupytext percent file."""
    marks = list(CELL_RE.finditer(source))
    cells = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(source)
        cells.append((m.group(1).strip(), source[m.end() : end]))
    return cells


def secret_keys() -> list[str]:
    return sorted(k for k in os.environ if k in SCRUB or SECRET_NAME_RE.search(k))


def scrub_environment() -> None:
    """Drop secrets from os.environ and make every dotenv loader a no-op, before any cell runs."""
    early = [m for m in sys.modules if m == "cua" or m.startswith("cua.")]
    if early:
        raise RuntimeError(f"cua modules imported before the scrub (may hold secrets): {early}")
    for key in secret_keys():
        os.environ.pop(key, None)
    try:
        import dotenv
        import dotenv.main
    except ImportError:
        return
    for mod in (dotenv, dotenv.main):
        mod.load_dotenv = lambda *a, **k: False  # type: ignore[assignment]
        mod.dotenv_values = lambda *a, **k: {}  # type: ignore[assignment]


def run_cell(path: pathlib.Path, header: str, body: str, ns: dict[str, object]) -> bool:
    if PLAYWRIGHT_RE.search(body):
        print(f"FAIL {header}: OFFLINE cells must not import playwright")
        return False
    start = time.time()
    try:
        exec(compile(body, f"{path.name}::{header}", "exec"), ns)
    except Exception:
        print(f"FAIL {header} ({path.name})")
        traceback.print_exc()
        return False
    print(f"   ({time.time() - start:.2f}s) {header}")
    return True


def post_run_checks() -> bool:
    leaked = secret_keys()
    if leaked:
        print(f"FAIL: secrets found in os.environ after the run: {leaked}")
    if "playwright" in sys.modules:
        print("FAIL: playwright was imported during the OFFLINE run")
    return not leaked and "playwright" not in sys.modules


def run(paths: list[pathlib.Path]) -> int:
    scrub_environment()
    sys.meta_path.insert(0, PlaywrightBlocker())
    # A real module object, like a Jupyter kernel's __main__: dataclasses/typing look up
    # sys.modules[cls.__module__], so a bare dict namespace breaks `from __future__ import annotations`.
    module = types.ModuleType("__discovery_offline__")
    sys.modules[module.__name__] = module
    ran = 0
    for path in paths:
        for header, body in split_cells(path.read_text()):
            if not OFFLINE_RE.match(header):
                continue
            if not run_cell(path, header, body, module.__dict__):
                return 1
            ran += 1
    if not post_run_checks():
        return 1
    print(f"ALL OFFLINE CELLS PASSED ({ran} cells)")
    return 0


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    args = [pathlib.Path(a) for a in sys.argv[1:]] or [here / "discovery.py"]
    sys.exit(run(args))

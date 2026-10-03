"""Brief 3.4: no session token and no raw account id is ever stored. Scans every text file under
``evidence/`` and ``artifacts/`` (offline, no browser) with the project's own id rule
(``IdMask.for_site``): an id must already be in its masked form ('***455')."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from cua.config import load_site
from cua.safety.redact import IdMask

ROOT = Path(__file__).resolve().parents[2]
TEXT = {".jsonl", ".json", ".txt", ".yaml", ".yml", ".md"}
SESSION = re.compile(r"jsessionid=[^\s\"';&?#]+", re.IGNORECASE)
IDS = IdMask.for_site(load_site("parabank"))


def _text_files() -> list[Path]:
    files = [p for d in ("evidence", "artifacts") for p in (ROOT / d).rglob("*")]
    return sorted(p for p in files if p.is_file() and p.suffix in TEXT)


def _strings(obj: object) -> Iterator[str]:
    """Every string in a JSON value, keys included (numbers are counts and pixels, never ids)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _texts(path: Path) -> Iterator[str]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        for line in raw.splitlines():
            if line.strip():
                yield from _strings(json.loads(line))
    elif path.suffix == ".json":
        yield from _strings(json.loads(raw))
    else:
        yield raw


FILES = _text_files()


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def test_the_scan_finds_the_evidence() -> None:
    assert any(p.suffix == ".jsonl" for p in FILES)


@pytest.mark.parametrize("path", FILES, ids=_rel)
def test_stored_text_never_holds_a_session_token(path: Path) -> None:
    leaks = [m.group() for t in _texts(path) for m in SESSION.finditer(t)]
    assert not leaks, f"{_rel(path)}: {len(leaks)} session token(s)"


@pytest.mark.parametrize("path", FILES, ids=_rel)
def test_stored_text_never_holds_a_raw_account_id(path: Path) -> None:
    raw = sorted({m.group() for t in _texts(path) for m in IDS.pattern.finditer(t)})
    assert not raw, f"{_rel(path)}: unmasked id(s) {raw}"

"""The frozen notebook snapshots the parity tests read must never drift (see _snapshots/)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tests.unit._snapshots import DISCOVERY, REPLAY

PINNED = {
    DISCOVERY: "155e192097cd1eb2b58af72dde001964babcca66e6d2f03c620aa1a59b287f43",
    REPLAY: "12206eb6e1e7953793986fdb02abf37e1417e2a2d8a6fba9cdd5704444f3def8",
}


@pytest.mark.parametrize("path", list(PINNED), ids=lambda p: p.name)
def test_snapshot_is_unchanged(path: Path) -> None:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == PINNED[path]

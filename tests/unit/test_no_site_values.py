"""Guard: no site value lives in src/. Site values belong in configs/<site>.yaml only."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
SITE = re.compile(r"parabank|parasoft", re.IGNORECASE)


def test_no_site_value_in_src() -> None:
    hits = [
        f"{path.relative_to(SRC)}:{n}"
        for path in sorted(SRC.rglob("*.py"))
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if SITE.search(line)
    ]
    assert not hits, hits

"""Value types an extract may declare. Shared by discovery and replay (one table, not two)."""

from __future__ import annotations

import re

SHAPES = {  # a value's shape inside a longer box: generic, never a site's own format
    "phone": r"\+?\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}",
    "currency": r"-?\$-?[\d,]*\d(?:\.\d{2})?|-?[\d,]*\d\.\d{2}",  # a `$`, or exactly 2 decimals
    "date": r"\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}",
    "integer": r"-?\d+",
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "id": r"[A-Za-z]*\d[\w-]*",
}
# Every extract type: the shapes plus the three whole-box-only kinds.
TYPES = {"string": r"\S.*", "number": r"-?[\d,]*\.?\d+", "boolean": r"true|false|yes|no", **SHAPES}


def value_matches_type(value: str, value_type: str) -> bool:
    """True when the whole value is exactly that type (string, number, boolean, or a shape)."""
    return value_type in TYPES and bool(re.fullmatch(TYPES[value_type], value.strip(), re.I))

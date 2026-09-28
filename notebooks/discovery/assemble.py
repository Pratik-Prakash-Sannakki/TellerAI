"""Join the part files into the one notebook, discovery.py, in run order. Build-time helper only.

Order:
1. Every non-BROWSER cell (OFFLINE and markdown, header line kept), in part order
   p0, p1, p2, p3, p3b, p4. Missing parts (e.g. p3b) are skipped.
2. BROWSER cells in the order the user runs them: 0, 2, 2b, 3, 5, 6, 7, 8.
   (BROWSER 0 is the lock check and must run first; 2b is the sitemap, before the agent exists.)
   Every OFFLINE cell comes before every BROWSER cell, so no BROWSER cell can depend on an
   OFFLINE cell that has not run yet.

Usage: python assemble.py [--root DIR]   (DIR holds parts/ and receives discovery.py;
default: this file's folder). Then pair it with jupytext:
`jupytext --set-formats ipynb,py:percent discovery.py`.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
PARTS = ["p0_contract.py", "p1_vision.py", "p2_gates.py", "p4_browser.py", "p3_agent.py", "p3c_typing.py",
         "p3d_nav.py", "p3e_extract.py", "p3f_human.py", "p3b_agent.py", "p5_browser_cells.py", "p6_runs.py"]
BROWSER_ORDER = ["0", "2", "2b", "3", "5", "6", "7", "8"]
CELL_RE = re.compile(r"^# %%(.*)$", re.MULTILINE)
BROWSER_NUM = re.compile(r"^BROWSER\s+(\w+)")


def split_cells(source: str) -> list[tuple[str, str]]:
    """(header, full cell text INCLUDING its `# %%` line) for every cell. Text before the first
    `# %%` line (none in our parts) would be dropped, so refuse it instead."""
    marks = list(CELL_RE.finditer(source))
    if marks and source[: marks[0].start()].strip():
        raise ValueError("text before the first `# %%` cell")
    return [
        (m.group(1).strip(), source[m.start() : marks[i + 1].start() if i + 1 < len(marks) else len(source)])
        for i, m in enumerate(marks)
    ]


def collect(root: pathlib.Path) -> tuple[list[str], dict[str, str]]:
    offline: list[str] = []
    browser: dict[str, str] = {}
    for name in PARTS:
        path = root / "parts" / name
        if not path.exists():
            continue
        for header, text in split_cells(path.read_text()):
            m = BROWSER_NUM.match(header)
            if not m:
                offline.append(text)
            elif m.group(1) in browser:
                raise ValueError(f"duplicate BROWSER {m.group(1)} in {name}")
            else:
                browser[m.group(1)] = text
    return offline, browser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=pathlib.Path, default=HERE)
    root: pathlib.Path = parser.parse_args(argv).root
    try:
        offline, browser = collect(root)
    except ValueError as err:
        print(err)
        return 1
    missing = [n for n in BROWSER_ORDER if n not in browser]
    extra = [n for n in browser if n not in BROWSER_ORDER]
    if missing or extra:
        print(f"BROWSER cells missing={missing} unexpected={extra}")
        return 1
    cells = offline + [browser[n] for n in BROWSER_ORDER]
    # Two blank lines between cells (jupytext's own percent-format spacing).
    out = "\n\n\n".join(c.strip("\n") for c in cells) + "\n"
    (root / "discovery.py").write_text(out)
    print(f"wrote {root / 'discovery.py'}: {len(cells)} cells ({len(offline)} offline/markdown, {len(browser)} browser)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

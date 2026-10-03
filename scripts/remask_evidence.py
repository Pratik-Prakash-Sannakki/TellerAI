"""Re-mask stored evidence/artifact text in place (session tokens, raw account ids); idempotent.

Uses the project's own rules: ``no_session`` drops a URL's ``;jsessionid=...`` (its query is kept,
its ids then masked) and ``IdMask.for_site`` turns a raw id into '***455'. JSON strings only are
touched (numbers are counts and pixels); a changed JSONL line is re-serialized the way the writer
wrote it (``json.dumps``). PNGs are left alone (masked at write time).
Run: ``.venv/bin/python scripts/remask_evidence.py [root]``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from cua.config import load_site
from cua.safety.redact import IdMask, no_session

TEXT = {".jsonl", ".json", ".txt", ".yaml", ".yml", ".md"}
SESSION_URL = re.compile(r"https?://[^\s\"'<>]*;jsessionid=[^\s\"'<>]*", re.IGNORECASE)


def fix(text: str, ids: IdMask) -> str:
    return ids(SESSION_URL.sub(lambda m: no_session(m.group(), query=True), text))


def _walk(obj: object, ids: IdMask) -> object:
    if isinstance(obj, str):
        return fix(obj, ids)
    if isinstance(obj, dict):
        return {fix(k, ids): _walk(v, ids) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(v, ids) for v in obj]
    return obj


def remask(path: Path, ids: IdMask) -> bool:
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        out = []
        for line in raw.splitlines(keepends=True):
            body = line.rstrip("\n")
            if body.strip():
                obj = json.loads(body)
                new = _walk(obj, ids)
                if new != obj:
                    out.append(json.dumps(new, default=str) + line[len(body) :])
                    continue
            out.append(line)
        text = "".join(out)
    elif path.suffix == ".json":
        obj = json.loads(raw)
        new = _walk(obj, ids)
        text = raw if new == obj else json.dumps(new, indent=2) + "\n"
    else:
        text = fix(raw, ids)
    if text == raw:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main(root: Path) -> None:
    ids = IdMask.for_site(load_site("parabank", root))
    for d in ("evidence", "artifacts"):
        for p in sorted((root / d).rglob("*")):
            if p.is_file() and p.suffix in TEXT and remask(p, ids):
                print(f"re-masked {p.relative_to(root)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])

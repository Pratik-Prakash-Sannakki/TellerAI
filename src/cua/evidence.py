"""Evidence helpers shared by discovery and replay: masking a JSON-able tree, writing a masked PNG,
and the run's provenance for ``run.json``.

``_clean``/``_png`` moved unchanged from notebooks/replay/replay.py 1604-1618 (discovery's copies,
discovery.py 2248-2255 / 2307-2311, have the same bodies; pinned by a parity test). ``mask_png``
needs an OCR function, so ``_png`` takes it explicitly (the notebooks used their global ``ocr``).
``run_info`` is new (Decision 5): no values, only what produced the run.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import JsonValue

from cua.config import SiteProfile
from cua.safety.redact import IdMask, OcrFn, mask_png

Redact = Callable[[str], str]


def _clean(obj: object, redact: Redact) -> object:
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: _clean(v, redact) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_clean(v, redact) for v in obj]
    return obj


def _png(
    path: Path, png: bytes | None, redact: Redact, ocr_fn: OcrFn, ids: IdMask | None = None
) -> str | None:
    """A masked PNG: run values and secrets blacked out; with ``ids``, account ids down to their
    last digits."""
    if not png:
        return None
    path.write_bytes(mask_png(png, redact, ocr_fn, ids))
    return path.name


def git_sha(cwd: Path | None = None) -> str:
    """`git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return out.stdout.strip() or "unknown"


def config_hash(configs: Sequence[object], site: SiteProfile) -> str:
    """sha256 of the repr of the frozen configs plus the site name."""
    text = repr(tuple(configs)) + site.name
    return hashlib.sha256(text.encode()).hexdigest()


def run_info(
    prompt_version: str | None, model: str | None, configs: Sequence[object], site: SiteProfile
) -> dict[str, JsonValue]:
    """What ``run.json`` holds: prompt version, model, config hash, git sha. Never a value."""
    return {
        "prompt_version": prompt_version,
        "model": model,
        "config_hash": config_hash(configs, site),
        "git_sha": git_sha(),
    }

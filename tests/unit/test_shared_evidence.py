"""cua.evidence: _clean/_png match both notebooks' own copies; run_info holds provenance only."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

from cua import evidence
from cua.config import BrowserConfig, ReplayConfig, load_site
from cua.evidence import _clean, _png, config_hash, git_sha, run_info
from tests.unit._snapshots import DISCOVERY as SNAP_DISCOVERY
from tests.unit._snapshots import REPLAY as SNAP_REPLAY

ROOT = Path(__file__).parents[2]
NOTEBOOKS = [SNAP_DISCOVERY, SNAP_REPLAY]
SITE = load_site("parabank")


def _body(path: Path, name: str) -> str:
    fn = next(n for n in ast.parse(path.read_text()).body if getattr(n, "name", None) == name)
    return ast.dump(ast.Module(fn.body, []))  # type: ignore[attr-defined]


def test_both_notebooks_have_the_same_clean_and_png() -> None:
    for name in ("_clean", "_png"):
        assert _body(NOTEBOOKS[0], name) == _body(NOTEBOOKS[1], name)


def test_clean_matches_the_notebooks_copy() -> None:
    ns: dict[str, object] = {}
    src = ast.parse(NOTEBOOKS[1].read_text())
    fn = next(n for n in src.body if getattr(n, "name", None) == "_clean")
    exec(compile(ast.Module([fn], []), "nb", "exec"), ns)  # noqa: S102
    tree = {"a": "x 7", "b": ["7", ("7", 3)], "c": None, "d": {"e": "77 7"}}
    redact = lambda t: re.sub(r"\b7\b", "***", t)  # noqa: E731
    assert _clean(tree, redact) == ns["_clean"](tree, redact)  # type: ignore[operator]


def test_png_writes_the_masked_image_or_nothing(tmp_path: Path) -> None:
    assert _png(tmp_path / "a.png", None, str, lambda img: []) is None
    assert not (tmp_path / "a.png").exists()
    assert _png(tmp_path / "a.png", b"raw", str, lambda img: []) == "a.png"  # clean: written as is
    assert (tmp_path / "a.png").read_bytes() == b"raw"


def test_run_info_shape() -> None:
    info = run_info("v3", "sonnet", (BrowserConfig(), ReplayConfig()), SITE)
    assert info["prompt_version"] == "v3"
    assert info["model"] == "sonnet"
    assert info["config_hash"] == config_hash((BrowserConfig(), ReplayConfig()), SITE)
    assert info["git_sha"] == git_sha()


def test_config_hash_changes_with_a_config() -> None:
    a = config_hash((ReplayConfig(),), SITE)
    assert a != config_hash((ReplayConfig(fuzzy=0.5),), SITE)
    assert a == config_hash((ReplayConfig(),), SITE)


def test_git_sha_falls_back_to_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **k: object) -> None:
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(evidence.subprocess, "run", boom)
    assert git_sha() == "unknown"

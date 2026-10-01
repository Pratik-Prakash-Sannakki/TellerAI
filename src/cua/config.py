"""Shared configuration: the site profile, browser/discovery/replay settings, and the Iliad gateway.

Site values (start URL, hosts, secret env-var names, words, outcome rules) live only in
``configs/<site>.yaml`` and are loaded into a frozen :class:`SiteProfile` by :func:`load_site`.
Nothing here is agent or replay logic.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv

load_dotenv(override=True)

# Company Iliad gateway (every LLM call goes here; see cua.llm). The key is read only from
# the ILIAD_API_KEY env var, inside cua.llm -- never stored in this module. `or` so a blank
# `.env` line (e.g. `ILIAD_BASE_URL=`) still means "use the default".
ILIAD_BASE_URL = os.getenv("ILIAD_BASE_URL") or "https://iliad-emerging-api.abbvienet.com/anthropic"
SONNET_MODEL_NAME = os.getenv("ILIAD_SONNET_MODEL") or "claude-sonnet-4-5-20250929"
HAIKU_MODEL_NAME = os.getenv("ILIAD_HAIKU_MODEL") or "claude-haiku-4-5-20251001"

OUTCOME_STATUSES = frozenset({"BUSINESS_OUTCOME", "RECOVER", "FAILED"})  # replay's load_outcomes


@dataclass(frozen=True)
class OutcomeRule:
    """R17: text seen after a step -> status. First match wins."""

    text: str
    status: str
    meaning: str


@dataclass(frozen=True)
class SiteProfile:
    """Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env NAMES only."""

    name: str
    start_url: str
    allowed_hosts: frozenset[str]
    secret_env: tuple[tuple[str, str], ...] = ()  # (secret name, env var name) pairs
    deny_words: frozenset[str] = frozenset()  # refused outright (D33)
    login_words: frozenset[str] = frozenset()
    login_failure_texts: tuple[str, ...] = ()
    outcomes: tuple[OutcomeRule, ...] = ()

    @property
    def base_url(self) -> str:
        return self.start_url.rstrip("/")

    @property
    def secrets(self) -> Mapping[str, str]:
        """Secret name -> env var name."""
        return dict(self.secret_env)


@dataclass(frozen=True)
class BrowserConfig:
    """Settings shared by discovery and replay (the same page size at both, Q10)."""

    viewport: tuple[int, int] = (1280, 800)
    ocr_min_score: float = 0.5
    scroll_px: int = 600
    same_screen_mad: float = 1.0  # mean pixel diff below this = "nothing changed"
    crop_pad: int = 6
    point_crop: tuple[int, int] = (160, 34)
    settle_ms: int = 600
    sensitive_words: frozenset[str] = frozenset({"password", "ssn", "social"})  # D34
    ext_s: float = 1.0  # any one call into the hand-back extension gives up after this
    ext_poll_s: float = 0.5  # take-over: how often the toolbar button's clicks are read


@dataclass(frozen=True)
class DiscoveryConfig:
    """Discovery-only settings."""

    send_wait_ms: int = 8000  # after an approved send: how long to wait for the response
    snap_ms: int = 3000  # an evidence screenshot gives up after this, never crashes a run
    handback_s: int = 120  # after Done: how long a send the human started may stay held
    login_limit: int = 3  # D69
    repeat_limit: int = 3
    unsure_limit: int = 3  # failed tool results in a row = the agent is unsure
    step_budget: int = 40  # tool calls per run before it counts as a loop


@dataclass(frozen=True)
class ReplayConfig:
    """Replay-only settings."""

    fuzzy: float = 0.8  # rung 1/2 text similarity (words only; digits match exactly)
    template_threshold: float = 0.8  # rung 3 matchTemplate score
    template_margin: float = 0.05  # a second peak this close to the best = ambiguous = miss
    scroll_retries: int = 1  # all rungs miss -> scroll down, retry this many times
    check_s: float = 5.0  # OCR poll budget for an `expect` check
    poll_ms: int = 200
    snap_s: float = 3.0  # evidence screenshot budget; a held send can block screenshots
    page_s: float = 2.0  # any other page read near a send (evaluate can block too)
    gate_s: float = 120.0  # hand-back waits this long for a send still at the gates
    field_min: tuple[int, int] = (40, 16)  # smallest drawn box that counts as an input field
    short_value: int = 2  # a typed value this short is checked by pixels if OCR misses it
    near_px: float = 60.0  # rung 1 with duplicate text: a copy this close to the anchor's point


def _find_root(start: Path) -> Path | None:
    """The nearest folder at or above `start` that has a ``configs/`` folder."""
    for folder in (start, *start.parents):
        if (folder / "configs").is_dir():
            return folder
    return None


def _repo_root() -> Path:
    found = _find_root(Path(__file__).resolve().parent) or _find_root(Path.cwd().resolve())
    if found is None:
        raise FileNotFoundError("no configs/ folder found above cua or the working directory")
    return found


def _outcomes(rules: list[dict[str, str]], path: Path) -> tuple[OutcomeRule, ...]:
    if bad := [r for r in rules if r.get("status") not in OUTCOME_STATUSES]:
        raise ValueError(f"{path}: outcomes with an unknown status: {bad}")
    return tuple(OutcomeRule(r["text"], r["status"], r.get("meaning", "")) for r in rules)


def load_site(name: str, root: Path | None = None) -> SiteProfile:
    """Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)."""
    path = (root or _repo_root()) / "configs" / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no site profile {name!r}: {path} does not exist")
    data = yaml.safe_load(path.read_text()) or {}
    return SiteProfile(
        name=data.get("name", name),
        start_url=data["start_url"],
        allowed_hosts=frozenset(data["allowed_hosts"]),
        secret_env=tuple((data.get("secret_env") or {}).items()),
        deny_words=frozenset(data.get("deny_words") or ()),
        login_words=frozenset(data.get("login_words") or ()),
        login_failure_texts=tuple(data.get("login_failure_texts") or ()),
        outcomes=_outcomes(data.get("outcomes") or [], path),
    )


def resolve_secret(name: str, site: SiteProfile) -> str:
    """Look up a secret by NAME. Raises on an unknown name or an empty/missing value.

    The value is read from `.env` only (D32) -- never hardcoded, never logged. Callers only ever
    pass a name (e.g. ``"password"``); the value itself should never be assigned to a variable
    that could end up in a log line or a saved artifact.
    """
    secrets = site.secrets
    if name not in secrets:
        raise KeyError(f"unknown secret name: {name!r}")
    value = os.environ.get(secrets[name], "")
    if not value:
        raise RuntimeError(f"env var {secrets[name]} is empty or not set")
    return value


def host_allowed(url: str, site: SiteProfile) -> bool:
    """True if `url`'s host is on the site's allowlist (D15). ``about:blank`` is always allowed
    (the browser's own blank starting page, not a real navigation anywhere)."""
    if url == "about:blank":
        return True
    return urlparse(url).hostname in site.allowed_hosts

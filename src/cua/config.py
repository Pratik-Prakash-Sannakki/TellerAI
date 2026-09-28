"""Shared configuration: the app this whole system points at, and secret lookup.

Ported from the identical config cells duplicated three times across the notebooks
(``agent.ipynb`` Setup 1/4, ``03_recorder.py`` OFFLINE 1 + BROWSER 1, ``05_replay_live.py``
Setup 1) -- see DECISIONS.md's Phase 9 packaging decision for why this one module now holds a
single copy instead of three. Every value below is config, per CLAUDE.md's own rule ("No
ParaBank-specific code in agent tools. ParaBank values live in config or ground-truth cells
only.") -- nothing here is agent or replay logic.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(override=True)

BASE = "https://parabank.parasoft.com/parabank"
ALLOWED_HOSTS = {"parabank.parasoft.com"}
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}   # names only (D32)
APP_ID = "parabank"
SESSION_EXPIRED_TEXT = "Customer Login"   # login page text, used for the relogin outcome rule

# Optional (D50): routes discovery steps to Haiku or Sonnet via TypeSafe. Off unless set.
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")

# Company Iliad gateway (every LLM call goes here; see cua.models). The key is read only from
# the ILIAD_API_KEY env var, inside cua.models -- never stored in this module. `or` so a blank
# `.env` line (e.g. `ILIAD_BASE_URL=`) still means "use the default".
ILIAD_BASE_URL = os.getenv("ILIAD_BASE_URL") or "https://iliad-emerging-api.abbvienet.com/anthropic"
SONNET_MODEL_NAME = os.getenv("ILIAD_SONNET_MODEL") or "claude-sonnet-4-5-20250929"
HAIKU_MODEL_NAME = os.getenv("ILIAD_HAIKU_MODEL") or "claude-haiku-4-5-20251001"


def resolve_secret(name: str) -> str:
    """Look up a secret by NAME. Raises on an unknown name or an empty/missing value.

    The value is read from `.env` only (D32) -- never hardcoded, never logged. Callers only ever
    pass a name (e.g. ``"password"``); the value itself should never be assigned to a variable
    that could end up in a log line or a saved artifact.
    """
    if name not in SECRETS:
        raise KeyError(f"unknown secret name: {name!r}")
    value = os.environ.get(SECRETS[name], "")
    if not value:
        raise RuntimeError(f"env var {SECRETS[name]} is empty or not set")
    return value


def host_allowed(url: str) -> bool:
    """True if `url`'s host is on the allowlist (D15). ``about:blank`` is always allowed (the
    browser's own blank starting page, not a real navigation anywhere)."""
    if url == "about:blank":
        return True
    return urlparse(url).hostname in ALLOWED_HOSTS

"""Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads `.env`)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fake_llm_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fake direct-Anthropic key so code that builds a chat model works offline; no gateway."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    for name in ("ILIAD_API_KEY", "ILIAD_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

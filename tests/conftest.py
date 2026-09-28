"""Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads `.env`)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fake_llm_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fake Iliad key so code that builds a chat model works offline; no real key is used."""
    monkeypatch.setenv("ILIAD_API_KEY", "test-key-not-real")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

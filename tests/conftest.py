"""Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads `.env`)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fake_llm_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fake Anthropic key so code that builds a chat model works offline."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

"""The one place that builds a chat model. Every LLM call in the project goes through here.

Default: the company Iliad gateway, via ``ChatAnthropic(anthropic_api_url=ILIAD_BASE_URL, ...)``
with the key from the ``ILIAD_API_KEY`` env var (loaded from the git-ignored `.env`).

Fallback (kept so the old setup still works): if ``ILIAD_API_KEY`` is unset but
``ANTHROPIC_API_KEY`` is set, build a plain ``ChatAnthropic(model_name=...)`` against Anthropic's
own API and say so once. With neither key, raise a clear ``RuntimeError``.

TLS: the gateway is internal and may need the corporate CA. httpx (used by the Anthropic SDK)
already honours ``SSL_CERT_FILE``; if only ``REQUESTS_CA_BUNDLE`` is set, it is copied to
``SSL_CERT_FILE``. Verification is never turned off.

The key value is never printed, logged or put in an error message. ``ChatAnthropic`` stores it as
a pydantic ``SecretStr``, so ``repr(model)`` shows ``**********``.
"""

from __future__ import annotations

import os
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from cua import config

ModelKind = Literal["sonnet", "haiku"]

_FALLBACK_NOTED = False   # the fallback notice is printed once per process


def model_name_for(kind: ModelKind) -> str:
    """The configured model name for `kind` (``ILIAD_SONNET_MODEL`` / ``ILIAD_HAIKU_MODEL``)."""
    names = {"sonnet": config.SONNET_MODEL_NAME, "haiku": config.HAIKU_MODEL_NAME}
    if kind not in names:
        raise ValueError(f"unknown model kind {kind!r}; expected 'sonnet' or 'haiku'")
    return names[kind]


def _pass_through_ca_bundle() -> None:
    """Let httpx pick up a corporate CA given as REQUESTS_CA_BUNDLE. Never disables checks."""
    bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
    if bundle and not os.environ.get("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = bundle


def _note_fallback() -> None:
    global _FALLBACK_NOTED
    if not _FALLBACK_NOTED:
        print("ILIAD_API_KEY not set; falling back to ANTHROPIC_API_KEY (Anthropic's own API).")
        _FALLBACK_NOTED = True


def make_chat_model(kind: ModelKind = "sonnet", **overrides: object) -> BaseChatModel:
    """Build the Sonnet or Haiku chat model, through the Iliad gateway by default.

    `overrides` are passed to ``ChatAnthropic`` (e.g. ``max_tokens=...``, ``temperature=...``).
    """
    name = model_name_for(kind)
    _pass_through_ca_bundle()
    iliad_key = os.environ.get("ILIAD_API_KEY", "")
    if iliad_key:
        return ChatAnthropic(anthropic_api_url=config.ILIAD_BASE_URL, api_key=iliad_key,
                             model_name=name, **overrides)
    if os.environ.get("ANTHROPIC_API_KEY", ""):
        _note_fallback()
        return ChatAnthropic(model_name=name, **overrides)   # key read from env by the library
    raise RuntimeError("ILIAD_API_KEY is not set in .env")

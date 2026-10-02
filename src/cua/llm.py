"""The one place that builds a chat model. Every LLM call in the project goes through here.

Direct Anthropic only: a plain ``ChatAnthropic(model_name=...)`` with the key from the
``ANTHROPIC_API_KEY`` env var (loaded from the git-ignored `.env`), against Anthropic's own API.
With no key, raise a clear ``RuntimeError``.

TLS: a corporate network may need its own CA. httpx (used by the Anthropic SDK) already honours
``SSL_CERT_FILE``; if only ``REQUESTS_CA_BUNDLE`` is set, it is copied to ``SSL_CERT_FILE``.
Verification is never turned off.

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
ANTHROPIC_API_URL = "https://api.anthropic.com"


def model_name_for(kind: ModelKind) -> str:
    """The model name for `kind` (``config.SONNET_MODEL_NAME`` / ``config.HAIKU_MODEL_NAME``)."""
    names = {"sonnet": config.SONNET_MODEL_NAME, "haiku": config.HAIKU_MODEL_NAME}
    if kind not in names:
        raise ValueError(f"unknown model kind {kind!r}; expected 'sonnet' or 'haiku'")
    return names[kind]


def _pass_through_ca_bundle() -> None:
    """Let httpx pick up a corporate CA given as REQUESTS_CA_BUNDLE. Never disables checks."""
    bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
    if bundle and not os.environ.get("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = bundle


def _build(conn: dict[str, object], name: str, overrides: dict[str, object]) -> ChatAnthropic:
    """``ChatAnthropic(**conn, model_name=name, **overrides)``, built through ``model_validate``.

    ``model_validate`` runs the exact validator ``__init__`` runs, but takes a plain dict, so free
    ``overrides`` such as ``max_tokens`` (a field whose pydantic alias is ``max_tokens_to_sample``)
    type-check without mypy's alias-only ``__init__`` signature rejecting them.
    """
    # dict(**...) raises TypeError on a repeated key, exactly as a repeated keyword argument did.
    return ChatAnthropic.model_validate(dict(**conn, model_name=name, **overrides))


def make_chat_model(kind: ModelKind = "sonnet", **overrides: object) -> BaseChatModel:
    """Build the Sonnet or Haiku chat model, direct Anthropic.

    `overrides` are passed to ``ChatAnthropic`` (e.g. ``max_tokens=...``, ``temperature=...``).
    """
    name = model_name_for(kind)
    _pass_through_ca_bundle()
    if not os.environ.get("ANTHROPIC_API_KEY", ""):
        raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")
    # Anthropic's own API, always: a stray ANTHROPIC_BASE_URL in the shell never redirects calls.
    return _build({"anthropic_api_url": ANTHROPIC_API_URL}, name, overrides)

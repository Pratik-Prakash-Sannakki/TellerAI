"""Backward-compatible alias: the chat-model factory now lives in :mod:`cua.llm`."""

from cua.llm import ModelKind, make_chat_model  # noqa: F401

__all__ = ["ModelKind", "make_chat_model"]

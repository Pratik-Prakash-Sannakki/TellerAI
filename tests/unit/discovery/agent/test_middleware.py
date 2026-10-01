"""LatestScreenshotOnly keeps only the newest image in the model's context; the no-op caching
middleware passes the request through untouched. Ported from
tests/discovery/test_latest_screenshot.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, ToolMessage

from cua.discovery.agent.middleware import (
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
)


def _shot(i: int) -> ToolMessage:
    return ToolMessage(
        tool_call_id=str(i),
        content=[
            {"type": "text", "text": f"look {i}"},
            {"type": "image", "base64": "x", "mime_type": "image/png"},
        ],
    )


def _req() -> SimpleNamespace:
    msgs = [HumanMessage("goal"), _shot(1), _shot(2), _shot(3)]
    return SimpleNamespace(messages=msgs, override=lambda messages: messages)


def test_only_last_image_survives() -> None:
    out = LatestScreenshotOnly()._trim(_req())
    images = [sum(b.get("type") == "image" for b in m.content) for m in out[1:]]
    assert images == [0, 0, 1]
    assert [m.content[0]["text"] for m in out[1:]] == ["look 1", "look 2", "look 3"]


@pytest.mark.asyncio
async def test_async_call_trims_too() -> None:
    async def handler(msgs: list[object]) -> list[object]:
        return msgs

    out = await LatestScreenshotOnly().awrap_model_call(_req(), handler)  # type: ignore[arg-type]
    assert [sum(b.get("type") == "image" for b in m.content) for m in out[1:]] == [0, 0, 1]


@pytest.mark.asyncio
async def test_noop_caching_passes_the_request_through() -> None:
    mw, req = NoopAnthropicPromptCachingMiddleware(), object()
    assert mw.name == "AnthropicPromptCachingMiddleware"
    assert mw.wrap_model_call(req, lambda r: r) is req  # type: ignore[arg-type]

    async def handler(r: object) -> object:
        return r

    assert await mw.awrap_model_call(req, handler) is req  # type: ignore[arg-type]

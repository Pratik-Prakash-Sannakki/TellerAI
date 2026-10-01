"""LatestScreenshotOnly keeps only the newest image in the model's context; the no-op caching
middleware passes the request through untouched. Ported from
tests/discovery/test_latest_screenshot.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from cua.discovery.agent.middleware import (
    WHY_CHARS,
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
    RecordWhy,
)
from tests.fakes import make_ctx


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


def _answer(text: str, *calls: dict[str, object]) -> SimpleNamespace:
    msg = AIMessage(
        content=text,
        tool_calls=[
            {"name": c["name"], "args": c["args"], "id": f"c{i}"} for i, c in enumerate(calls)
        ],
    )
    return SimpleNamespace(result=[msg])


@pytest.mark.asyncio
async def test_record_why_keeps_the_text_before_a_tool_call() -> None:
    ctx = make_ctx()
    why = "The login form is open, so I type the username."
    resp = _answer(why, {"name": "observe", "args": {}})

    async def handler(r: object) -> object:
        return resp

    assert await RecordWhy(ctx).awrap_model_call(object(), handler) is resp  # type: ignore[arg-type]
    assert ctx.run.why == why


def test_record_why_masks_values_secrets_and_the_calls_own_args() -> None:
    ctx = make_ctx(secrets={"username": "u-val", "password": "p-val"})
    ctx.run.typed_texts.add("Springfield")
    text = "Typed Springfield and u-val; now 74838 goes in To account, then p-val."
    resp = _answer(text, {"name": "type_text", "args": {"text": "74838", "ref": 3}})
    RecordWhy(ctx).wrap_model_call(object(), lambda r: resp)  # type: ignore[arg-type, return-value]
    why = ctx.run.why
    for value in ("Springfield", "u-val", "p-val", "74838"):
        assert value not in why
    assert "To account" in why


def test_record_why_is_truncated_after_masking() -> None:
    ctx = make_ctx()
    text = "x" * 195 + " 74838 and more words after it"
    resp = _answer(text, {"name": "type_text", "args": {"text": "74838"}})
    RecordWhy(ctx).wrap_model_call(object(), lambda r: resp)  # type: ignore[arg-type, return-value]
    assert len(ctx.run.why) <= WHY_CHARS
    assert "7483" not in ctx.run.why  # masked first, so no prefix of the value survives


def test_record_why_ignores_an_answer_with_no_tool_call() -> None:
    ctx = make_ctx()
    ctx.run.why = "earlier"
    RecordWhy(ctx).wrap_model_call(object(), lambda r: _answer("Done."))  # type: ignore[arg-type, return-value]
    assert ctx.run.why == "earlier"


def test_record_why_reads_text_blocks() -> None:
    ctx = make_ctx()
    msg = AIMessage(
        content=[{"type": "text", "text": "Opening bill pay."}],
        tool_calls=[{"name": "open_path", "args": {"path": "/billpay.htm"}, "id": "c0"}],
    )
    RecordWhy(ctx).wrap_model_call(object(), lambda r: SimpleNamespace(result=[msg]))  # type: ignore[arg-type, return-value]
    assert ctx.run.why == "Opening bill pay."


@pytest.mark.parametrize(
    "shown",
    [
        "13344",
        "1334 4556",
        "$1,250.00",
        "75.50",
        "jo.doe@example.test",
        "(555) 010-0199",
        "9/30/2026",
    ],
)
def test_record_why_blanks_value_shapes_seen_only_in_the_ai_text(shown: str) -> None:
    ctx = make_ctx()  # the value is no run value and no tool arg: only its shape gives it away
    resp = _answer(
        f"I see {shown} on screen, so I open the next page.", {"name": "observe", "args": {}}
    )
    RecordWhy(ctx).wrap_model_call(object(), lambda r: resp)  # type: ignore[arg-type, return-value]
    assert shown not in ctx.run.why
    assert ctx.run.why == "I see [value] on screen, so I open the next page."


def test_record_why_keeps_short_numbers_like_refs() -> None:
    ctx = make_ctx()
    resp = _answer("Box 12 is the Payee Name field.", {"name": "observe", "args": {}})
    RecordWhy(ctx).wrap_model_call(object(), lambda r: resp)  # type: ignore[arg-type, return-value]
    assert ctx.run.why == "Box 12 is the Payee Name field."

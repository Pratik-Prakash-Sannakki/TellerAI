"""finish_business_outcome / request_missing_values / ask_human (the human-facing @tools)."""

from __future__ import annotations

import pytest

from cua.discovery.context import Ctx
from cua.discovery.tools import human
from cua.discovery.tools.human import make_human_tools, start_page_refusal
from tests.fakes import ActTab, blank_png, make_ctx, make_look, make_session

PNG = blank_png()
FORM = make_look([("Amount:", (10, 100, 80, 120))], png=PNG)


def _tool(ctx: Ctx, name: str):  # type: ignore[no-untyped-def]
    return {t.name: t for t in make_human_tools(ctx)}[name]


def _ctx(url: str = "https://example.test/app/billpay.htm") -> Ctx:
    ctx = make_ctx(make_session(ActTab(url)))
    ctx.run.look = FORM
    return ctx


@pytest.mark.asyncio
async def test_finish_needs_the_proof_on_the_screen() -> None:
    ctx = _ctx()
    tool = _tool(ctx, "finish_business_outcome")
    assert (await tool.ainvoke({"outcome": "paid", "proof_text": "Done!"})).startswith("REFUSED")
    assert await tool.ainvoke({"outcome": "paid", "proof_text": "amount"}) == "OK"
    assert ctx.run.log[-1]["args"] == {"outcome": "paid", "proof_text": "amount"}


def test_the_start_page_is_too_early_for_form_values() -> None:
    assert start_page_refusal(_ctx("https://example.test/app/;jsessionid=1")) is not None
    assert start_page_refusal(_ctx()) is None


@pytest.mark.asyncio
async def test_request_missing_values_refuses_on_the_start_page() -> None:
    ctx = _ctx("https://example.test/app/")
    out = await _tool(ctx, "request_missing_values").ainvoke(
        {"fields": [{"x": 100, "y": 110, "hint": "Amount"}]}
    )
    assert out[0]["text"].startswith("NOT YET: you are on the start page.")


@pytest.mark.asyncio
async def test_request_missing_values_hands_each_field_and_its_kind_to_the_human(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx, asked = _ctx(), []

    async def fills(ctx: Ctx, fields: list[object], **kw: object) -> str:
        asked.append((fields, kw))
        return "A human gave: Amount, Account."

    monkeypatch.setattr(human, "human_fills", fills)
    fields = [
        {"x": 100, "y": 110, "hint": "Amount"},
        {"x": 300, "y": 110, "hint": "Account", "dropdown": True},
    ]
    out = await _tool(ctx, "request_missing_values").ainvoke({"fields": fields})
    assert out[0]["text"].startswith("A human gave")
    assert asked == [
        ([((100, 110), "Amount"), ((300, 110), "Account")], {"dropdowns": [False, True]})
    ]


@pytest.mark.asyncio
async def test_request_missing_values_refuses_a_point_off_the_screen() -> None:
    ctx = _ctx()
    out = await _tool(ctx, "request_missing_values").ainvoke(
        {"fields": [{"x": 5000, "y": 110, "hint": "Amount"}]}
    )
    assert out[0]["text"].startswith("OUT OF VIEW: (5000,110)")


@pytest.mark.asyncio
async def test_no_fields_given() -> None:
    out = await _tool(_ctx(), "request_missing_values").ainvoke({"fields": []})
    assert out[0]["text"].startswith("No fields given.")


@pytest.mark.asyncio
async def test_ask_human_asks_with_the_question(monkeypatch: pytest.MonkeyPatch) -> None:
    asked: list[tuple[str, str]] = []

    async def help_(ctx: Ctx, title: str, reason: str) -> str:
        asked.append((title, reason))
        return "The human says: pick savings"

    monkeypatch.setattr(human, "human_help", help_)
    out = await _tool(_ctx(), "ask_human").ainvoke({"question": "Which account?"})
    assert out == "The human says: pick savings"
    assert asked == [("The agent asks", "Which account?")]

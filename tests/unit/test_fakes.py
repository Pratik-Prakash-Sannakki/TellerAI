"""Tests for the shared offline fakes in tests/fakes.py (TDD: written before the fakes)."""

from __future__ import annotations

import pytest

from tests.fakes import FakeControl, FakePage, FakeRoute


class TestFakeRoute:
    def test_records_the_request_fields(self) -> None:
        route = FakeRoute(
            method="POST",
            url="https://example.test/pay",
            post_data="amount=10",
            headers={"X-Test": "1"},
        )
        assert route.request.method == "POST"
        assert route.request.url == "https://example.test/pay"
        assert route.request.post_data == "amount=10"
        assert route.request.headers == {"X-Test": "1"}

    def test_defaults_are_a_plain_get_with_no_body(self) -> None:
        route = FakeRoute()
        assert route.request.method == "GET"
        assert route.request.post_data is None
        assert route.request.headers == {}

    @pytest.mark.asyncio
    async def test_continue_abort_fulfill_are_each_recorded(self) -> None:
        route = FakeRoute()
        await route.continue_(url="https://example.test/next")
        await route.abort()
        await route.fulfill(status=200)
        assert route.calls == [
            ("continue_", {"url": "https://example.test/next"}),
            ("abort", {}),
            ("fulfill", {"status": 200}),
        ]


class TestFakePage:
    def test_url_attribute_is_settable_and_readable(self) -> None:
        page = FakePage(url="https://example.test/start")
        assert page.url == "https://example.test/start"

    @pytest.mark.asyncio
    async def test_screenshot_and_evaluate_are_recorded(self) -> None:
        page = FakePage()
        shot = await page.screenshot()
        result = await page.evaluate("() => 1", "arg")
        assert shot == b"shot"
        assert result is None
        assert page.calls[0] == ("screenshot", (), {})
        assert page.calls[1] == ("evaluate", ("() => 1", "arg"), {})

    def test_on_and_remove_listener_are_recorded(self) -> None:
        page = FakePage()

        def handler(frame: object) -> None:
            del frame

        page.on("framenavigated", handler)
        page.remove_listener("framenavigated", handler)
        assert page.calls == [
            ("on", ("framenavigated", handler), {}),
            ("remove_listener", ("framenavigated", handler), {}),
        ]

    @pytest.mark.asyncio
    async def test_raise_all_makes_every_awaited_method_raise(self) -> None:
        page = FakePage(raise_all=True)
        with pytest.raises(RuntimeError):
            await page.screenshot()
        with pytest.raises(RuntimeError):
            await page.evaluate("() => 1")
        with pytest.raises(RuntimeError):
            await page.wait_for_timeout(10)
        # the call is still recorded before the raise, so a test can see what was attempted
        assert [name for name, _args, _kwargs in page.calls] == [
            "screenshot",
            "evaluate",
            "wait_for_timeout",
        ]


class TestFakeControl:
    @pytest.mark.asyncio
    async def test_records_each_mode_shown(self) -> None:
        control = FakeControl("approve", "done")
        await control.ask("Gate", "details", "confirm")
        await control.ask("Takeover", "details", "rescue")
        assert control.asked == ["confirm", "rescue"]

    @pytest.mark.asyncio
    async def test_returns_queued_answers_in_order(self) -> None:
        control = FakeControl("approve", "done")
        first = await control.ask("Gate 1", "", "confirm")
        second = await control.ask("Gate 2", "", "confirm")
        assert first == "approve"
        assert second == "done"

    @pytest.mark.asyncio
    async def test_returns_none_once_answers_run_out(self) -> None:
        control = FakeControl()
        assert await control.ask("Gate", "", "confirm") is None

"""Shared offline fakes for the ported test suite (tests/unit, tests/integration).

Modeled on the fakes already scattered across tests/discovery/*.py and tests/replay/*.py
(``FakeWin``, ``FakeBox``, ``FakePage``, ``FakeControl``/``FakeLock`` and friends) -- this module
gives later steps one place to import them from instead of redefining them per test file. The old
fakes in tests/discovery/ and tests/replay/ are left alone; they are deleted only when the test
file that defines them is itself ported (see docs/PRODUCTIONIZE_PLAN.md section 6).

No Playwright import: these are plain, typed stand-ins for the Playwright objects the real code
touches (``Page``, a route handler's ``Route``) and for the discovery/replay control surface
(``ControlWindow``/``CONTROL``). Nothing here touches a browser, the network, or an LLM.
"""

from __future__ import annotations

from collections.abc import Mapping


class _Request:
    """The handful of ``playwright.async_api.Request`` fields the project's code reads."""

    def __init__(
        self,
        method: str,
        url: str,
        post_data: str | None,
        headers: Mapping[str, str],
    ) -> None:
        self.method = method
        self.url = url
        self.post_data = post_data
        self.headers = dict(headers)


class FakeRoute:
    """A fake ``playwright.async_api.Route``: records every ``continue_``/``abort``/``fulfill``.

    ``calls`` is an ordered list of ``(method_name, kwargs)`` pairs, so a test can assert both that
    a call happened and what it was called with (e.g. a rewritten ``post_data`` on ``continue_``).
    """

    def __init__(
        self,
        method: str = "GET",
        url: str = "https://example.test/",
        post_data: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.request = _Request(method, url, post_data, headers or {})
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def continue_(self, **kwargs: object) -> None:
        self.calls.append(("continue_", kwargs))

    async def abort(self, **kwargs: object) -> None:
        self.calls.append(("abort", kwargs))

    async def fulfill(self, **kwargs: object) -> None:
        self.calls.append(("fulfill", kwargs))


class FakePage:
    """A fake ``playwright.async_api.Page``.

    Every awaited method is recorded in ``calls`` as ``(name, args, kwargs)``, then returns a
    harmless default (``b"shot"`` for ``screenshot``, ``None`` otherwise). With ``raise_all=True``,
    every awaited method raises ``RuntimeError`` instead (after being recorded) -- for exercising
    "a held POST blocks every page call" style tests, where the real page would hang or fail.
    """

    def __init__(self, url: str = "https://example.test/", *, raise_all: bool = False) -> None:
        self.url = url
        self.raise_all = raise_all
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def _record(self, name: str, args: tuple[object, ...], kwargs: dict[str, object]) -> None:
        self.calls.append((name, args, kwargs))
        if self.raise_all:
            raise RuntimeError(f"FakePage.{name} raised (raise_all=True)")

    async def screenshot(self, *args: object, **kwargs: object) -> bytes:
        self._record("screenshot", args, kwargs)
        return b"shot"

    async def evaluate(self, *args: object, **kwargs: object) -> None:
        self._record("evaluate", args, kwargs)

    async def wait_for_timeout(self, *args: object, **kwargs: object) -> None:
        self._record("wait_for_timeout", args, kwargs)

    def on(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("on", args, kwargs))

    def remove_listener(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("remove_listener", args, kwargs))


class FakeControl:
    """A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).

    ``ask`` records the ``mode`` it was shown for in ``asked`` and returns the next queued answer
    (``None`` once the queue is empty, so an unscripted extra call fails loudly rather than
    hanging).
    """

    def __init__(self, *answers: str) -> None:
        self.answers: list[str] = list(answers)
        self.asked: list[str] = []

    async def ask(self, title: str, details: str, mode: str, **_: object) -> str | None:
        del title, details
        self.asked.append(mode)
        return self.answers.pop(0) if self.answers else None

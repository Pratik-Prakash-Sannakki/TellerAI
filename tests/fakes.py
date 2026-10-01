"""Shared offline fakes for the ported test suite (tests/unit, tests/integration).

Modeled on the fakes already scattered across tests/discovery/*.py and tests/replay/*.py
(``FakeWin``, ``FakeBox``, ``FakePage``, ``FakeControl``/``FakeLock`` and friends) -- this module
gives later steps one place to import them from instead of redefining them per test file. The old
fakes in tests/discovery/ and tests/replay/ are left alone; they are deleted only when the test
file that defines them is itself ported (see docs/PRODUCTIONIZE_PLAN.md section 6).

Only Playwright's error type is imported: these are plain, typed stand-ins for the Playwright
objects the real code touches (``Page``, a route handler's ``Route``) and for the discovery/replay
control surface (``ControlWindow``/``CONTROL``). ``make_session``/``make_ctx`` build a discovery
``Ctx`` over these fakes. Nothing here touches a browser, the network, or an LLM.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Callable, Mapping
from types import SimpleNamespace

from playwright.async_api import Error as PlaywrightError

from cua.browser.session import Session
from cua.config import BrowserConfig, DiscoveryConfig, SiteProfile
from cua.discovery.context import Ctx
from cua.discovery.wiring import build_ctx, new_run
from cua.vision.ocr import RefCounter


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


class FakeLock:
    """A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else."""

    def __init__(self) -> None:
        self.log: list[str] = []

    async def set(self, locked: bool) -> None:
        self.log.append("lock" if locked else "unlock")

    @contextlib.asynccontextmanager
    async def open(self) -> AsyncIterator[None]:
        self.log.append("unlock")
        try:
            yield
        finally:
            self.log.append("lock")


class FakeTab:
    """A fake site or control tab with the Playwright calls discovery's wiring and take-over make.

    Fires ``framenavigated`` like Playwright (``navigate``), records route/unroute and every
    other call in ``calls``; ``expose_function`` raises "already registered" the second time.
    ``hangs=True`` makes ``screenshot`` time out (a send held at the gates).
    """

    def __init__(self, url: str = "https://example.test/x") -> None:
        self.url, self.main_frame = url, SimpleNamespace(url="")
        self.handlers: dict[str, list[Callable[..., object]]] = {}
        self.calls: list[str] = []
        self.routes: list[object] = []
        self.exposed: dict[str, Callable[..., object]] = {}
        self.html, self.closed, self.hangs, self.shots = "", False, False, 0

    def on(self, event: str, fn: Callable[..., object]) -> None:
        self.calls.append("on")
        self.handlers.setdefault(event, []).append(fn)

    def remove_listener(self, event: str, fn: Callable[..., object]) -> None:
        self.calls.append("remove_listener")
        self.handlers[event].remove(fn)

    def emit(self, event: str, arg: object) -> None:
        for fn in list(self.handlers.get(event, [])):
            fn(arg)

    def navigate(self, url: str, iframe: bool = False) -> None:
        frame = SimpleNamespace(url=url) if iframe else self.main_frame
        frame.url = url
        if not iframe:
            self.url = url
        self.emit("framenavigated", frame)

    async def screenshot(self, **_: object) -> bytes:
        self.calls.append("screenshot")
        self.shots += 1
        if self.hangs:
            raise PlaywrightError("Page.screenshot: Timeout 3000ms exceeded.")
        return f"shot{self.shots}".encode()

    async def wait_for_timeout(self, ms: float) -> None:
        self.calls.append("wait_for_timeout")

    async def goto(self, url: str) -> None:
        self.calls.append("goto")
        self.url = url

    async def unroute(self, pattern: str) -> None:
        self.calls.append("unroute")
        self.routes.clear()

    async def route(self, pattern: str, handler: object) -> None:
        self.calls.append("route")
        self.routes.append(handler)

    async def expose_function(self, name: str, fn: Callable[..., object]) -> None:
        self.calls.append("expose_function")
        if name in self.exposed:
            raise PlaywrightError(f'Function "{name}" has been already registered')
        self.exposed[name] = fn

    async def set_content(self, content: str) -> None:
        self.html = content

    def is_closed(self) -> bool:
        return self.closed

    async def bring_to_front(self) -> None:
        self.calls.append("bring_to_front")


def make_session(
    page: FakeTab | None = None,
    control_page: FakeTab | None = None,
    ext: object | None = None,
    cfg: BrowserConfig | None = None,
) -> Session:
    """A ``cua.browser.Session`` over fakes (no Playwright launched)."""
    return Session(
        pw=None,  # type: ignore[arg-type]
        context=None,  # type: ignore[arg-type]
        page=page or FakeTab(),  # type: ignore[arg-type]
        control_page=control_page or FakeTab("about:blank"),  # type: ignore[arg-type]
        ext=ext,  # type: ignore[arg-type]
        cfg=cfg or BrowserConfig(ext_s=0.05, ext_poll_s=0.01),
        site=SITE,
        lock=FakeLock(),  # type: ignore[arg-type]
        refs=RefCounter(),
    )


SITE = SiteProfile(
    name="test",
    start_url="https://example.test/app/",
    allowed_hosts=frozenset({"example.test"}),
    secret_env=(("username", "TEST_USER"), ("password", "TEST_PASS")),
    deny_words=frozenset({"register", "admin"}),
    login_words=frozenset({"log in"}),
    login_failure_texts=("could not be verified",),
)


def make_ctx(
    session: Session | None = None,
    cfg: DiscoveryConfig | None = None,
    secrets: Mapping[str, str] | None = None,
    goal: str = "",
) -> Ctx:
    """A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring."""
    ctx = build_ctx(
        session or make_session(),
        cfg or DiscoveryConfig(),
        {"username": "u-val", "password": "p-val"} if secrets is None else secrets,
    )
    return new_run(ctx, goal)

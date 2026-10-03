"""Ctx: what every replay function takes first (session, run, settings, send guard, control tab).

Replaces the notebook's globals (``page``, ``LOCK``, ``CONTROL``, ``EXT``, ``CFG``, ``SECRETS``,
``STATE``, ``SEND_GATE``, ``LAST_RUN``). Not frozen on purpose: ``replay()`` wipes the run in its
``finally`` (R7) by swapping ``ctx.run`` for a fresh :class:`ReplayRun` -- :func:`wipe` also points
the guard at it, as the notebook's ``STATE = ReplayState()`` did for ``guard_send``. Every other
field is set once.

The guard is built in ``__post_init__`` (inside the running loop) with replay's hooks: on_request
``run.sent = True`` + the take-over send path, on_gated ``run.gated = True``
(``REPLAY_OPTIONS``: Gate 2 decline text, image on take-over, ``None`` human edit options).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field

from playwright.async_api import Page

from cua.browser.session import Session
from cua.config import BrowserConfig, ReplayConfig, SiteProfile
from cua.handoff.control_window import ControlWindow
from cua.replay.run import LastRun, ReplayRun, url_path
from cua.safety.request import Request
from cua.safety.send_guard import REPLAY_OPTIONS, SendGuard, SendHooks
from cua.vision import Look

Shoot = Callable[[], Awaitable[Look]]


@dataclass
class Ctx:
    session: Session
    cfg: ReplayConfig
    control: ControlWindow
    secrets: Mapping[str, str]  # secret NAME -> value (from .env); never logged or shown
    shoot: Shoot  # screenshot -> numbered Look (vision.take_look on the site tab)
    run: ReplayRun = field(default_factory=ReplayRun)
    last: LastRun = field(default_factory=LastRun)
    guard: SendGuard = field(init=False)

    def __post_init__(self) -> None:
        hooks = SendHooks(on_request=self._on_request, on_gated=self._on_gated)
        words = self.session.cfg.sensitive_words
        self.guard = SendGuard(
            self.run, self.control, self.secrets, words, hooks, options=REPLAY_OPTIONS
        )

    @property
    def page(self) -> Page:
        return self.session.page

    @property
    def site(self) -> SiteProfile:
        return self.session.site

    @property
    def bcfg(self) -> BrowserConfig:
        return self.session.cfg

    def _on_request(self, req: Request) -> None:
        self.run.sent = True
        note_takeover_send(self, req.url)

    def _on_gated(self) -> None:
        self.run.gated = True


def note_takeover_send(ctx: Ctx, url: str) -> None:
    if ctx.run.takeover is not None:
        ctx.run.takeover["sends"].append(url_path(url))


def wipe(ctx: Ctx) -> None:
    """R7: nothing kept. A fresh run, and the guard reads that one from now on."""
    ctx.run = ReplayRun()
    ctx.guard.state = ctx.run

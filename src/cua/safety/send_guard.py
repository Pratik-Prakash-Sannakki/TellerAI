"""SendGuard: every request that sends data (not GET) is held for two human gates.

One guard for both sides (discovery.py 773-836 ``guard_send``, replay.py 457-506). Their bodies
are the same gates; every difference is an explicit :class:`GuardOptions` field or a
:class:`SendHooks` hook, so each side keeps its exact order and strings.

Nothing here touches the page (no evaluate, screenshot or locator): while a request is held, a
form POST (a navigation) keeps any page call from ever returning. The guard is never given a page.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from cua.safety.mismatch import dropdown_options, mismatches
from cua.safety.redact import hide_secrets, is_sensitive
from cua.safety.request import Request, pretty, rebuilt, sent_fields

PASS_METHODS = ("GET", "HEAD", "OPTIONS")
SENT = "SENT: a human approved both gates."
NOT_CONFIRMED = "STUCK: the details were not confirmed. Nothing was sent."


class LookLike(Protocol):
    @property
    def png(self) -> bytes: ...


class SendState(Protocol):
    """What the guard reads and writes on a run (DiscoveryRun / ReplayRun satisfy it)."""

    verdict: str

    @property
    def allow_send(self) -> bool: ...

    @property
    def takeover(self) -> object: ...

    @property
    def given(self) -> list[str]: ...

    @property
    def look(self) -> LookLike | None: ...

    @property
    def dropdowns(self) -> Sequence[Mapping[str, object]]: ...

    def given_text(self) -> str: ...


class ControlLike(Protocol):
    """The two ControlWindow calls the gates use."""

    async def ask(
        self, title: str, details: str, mode: str, image: bytes | None = None
    ) -> str | None: ...

    async def form(
        self,
        title: str,
        fields: list[tuple[str, bool]],
        values: list[str] | None = None,
        options: list[list[str]] | None = None,
    ) -> list[str] | None: ...


class RouteLike(Protocol):
    @property
    def request(self) -> Request: ...

    async def continue_(self, *, url: str | None = None, post_data: str | None = None) -> None: ...

    async def abort(self) -> None: ...


OnSent = Callable[[Request, dict[str, str], dict[str, str], LookLike | None], Awaitable[None]]
AfterVerdict = Callable[[Request, dict[str, str], dict[str, str], bool], None]


@dataclass(frozen=True)
class SendHooks:
    """Side-specific steps, each at the exact point its notebook ran it.

    on_request: replay -- right after the GET/HEAD/OPTIONS pass, before the allow_send check
        (``STATE.sent = True; note_takeover_send(url)``).
    on_gated: replay -- after allow_send did not pass (``STATE.gated = True``).
    on_sent(req, original, fields, look): discovery -- after Gate 2 approve, before the verdict
        (redact |= values, log_sent_dropdowns if look, entered = {}).
    after_verdict(req, original, fields, human): discovery -- after the SENT verdict, before the
        request goes (log("send"), take-over send path).
    """

    on_request: Callable[[Request], None] | None = None
    on_gated: Callable[[], None] | None = None
    on_sent: OnSent | None = None
    after_verdict: AfterVerdict | None = None


@dataclass(frozen=True)
class GuardOptions:
    """The two notebooks' differences, by name.

    human_in_lock: discovery reads ``takeover`` after taking the lock, replay before.
    image_on_takeover: replay shows its last look at the gates even for a human's send.
    plain_edit_boxes: a human's Gate 1 edit gets ``[[] ...]`` (discovery) or ``None`` (replay).
    """

    decline_text: str
    human_in_lock: bool
    image_on_takeover: bool
    plain_edit_boxes: bool


DISCOVERY_OPTIONS = GuardOptions(
    decline_text=(
        "DECLINED by a human. Do not retry or work around it. Reply 'DECLINED: <why>' and stop."
    ),
    human_in_lock=True,
    image_on_takeover=False,
    plain_edit_boxes=True,
)
REPLAY_OPTIONS = GuardOptions(
    decline_text="DECLINED: a human said no at Gate 2. Nothing was sent.",
    human_in_lock=False,
    image_on_takeover=True,
    plain_edit_boxes=False,
)


class SendGuard:
    """``await guard(route)`` is the route handler. ``guard.lock`` is the send gate: held while a
    request waits at the gates (act() waits on it). Build inside the running loop."""

    def __init__(  # noqa: PLR0913 (constraints allow 6)
        self,
        state: SendState,
        control: ControlLike,
        secrets: Mapping[str, str],
        sensitive_words: Iterable[str],
        hooks: SendHooks,
        *,
        options: GuardOptions,
    ) -> None:
        self.state, self.control, self.hooks, self.options = state, control, hooks, options
        self.secrets, self.words = secrets, frozenset(sensitive_words)
        self.lock = asyncio.Lock()

    async def __call__(self, route: RouteLike) -> None:
        req = route.request
        if req.method in PASS_METHODS:
            return await route.continue_()
        if self.hooks.on_request:
            self.hooks.on_request(req)
        if self.state.allow_send:
            return await route.continue_()
        if self.hooks.on_gated:
            self.hooks.on_gated()
        human = self.state.takeover is not None  # the human's own send: they chose every value
        async with self.lock:
            if self.options.human_in_lock:
                human = self.state.takeover is not None
            await self._held(route, human)

    async def _held(self, route: RouteLike, human: bool) -> None:
        req, st = route.request, self.state
        fields = sent_fields(req)
        original = dict(fields)
        # e.g. a dropdown left on its default: the human never gave that value. Ask them now,
        # with the page's value filled in, and send what they confirm. The send is only held.
        bad = [] if human else mismatches(fields, st.given_text(), self.words)
        if bad and not await self._confirm_mismatch(fields, bad):
            return await route.abort()
        # The last look is the page as filled (the agent's own send); discovery shows a human's
        # take-over send no image (none is current).
        look = None if human and not self.options.image_on_takeover else st.look
        shot = look.png if look else None  # dropped once values are edited
        what = await self._gate1(req, fields, original, shot, human)
        if what is None:  # control tab closed: fail closed
            st.verdict = NOT_CONFIRMED
            return await route.abort()
        url, body = rebuilt(req, fields) if fields != original else (req.url, req.post_data)
        if not await self._gate2(what, shot if fields == original else None):
            st.verdict = self.options.decline_text
            return await route.abort()
        if self.hooks.on_sent:
            await self.hooks.on_sent(req, original, fields, look)
        st.verdict = SENT
        if self.hooks.after_verdict:
            self.hooks.after_verdict(req, original, fields, human)
        await route.continue_(url=url, post_data=body)

    def _hide(self, text: str) -> str:
        return hide_secrets(text, self.secrets)

    def _options(self, fields: dict[str, str], keys: list[str]) -> list[list[str]]:
        return dropdown_options(fields, keys, self.state.dropdowns, self._hide)

    async def _confirm_mismatch(self, fields: dict[str, str], bad: list[str]) -> bool:
        opts = self._options(fields, bad)
        fixed = await self.control.form(
            "You never gave these. Check or correct them:",
            [(pretty(k), False) for k in bad],
            [fields[k] for k in bad],
            opts,
        )
        if not fixed or not all(fixed):
            self.state.verdict = (
                f"STUCK: No value confirmed for {', '.join(bad)}. Nothing was sent."
            )
            return False
        fields.update(zip(bad, fixed, strict=False))
        self.state.given.extend(fixed)
        return True

    def _details(self, url: str, fields: dict[str, str]) -> str:
        sent = self._hide(
            "\n".join(
                f"{pretty(k)}: {'******' if is_sensitive(k, self.words) else v}"
                for k, v in fields.items()
            )[:1200]
        )
        return f"Sending to {urlparse(url).path}:\n{sent or '(no fields)'}"

    async def _gate1(  # noqa: PLR0913 (constraints allow 6)
        self,
        req: Request,
        fields: dict[str, str],
        original: dict[str, str],
        shot: bytes | None,
        human: bool,
    ) -> str | None:
        """Gate 1: Approve, or Edit = back to the form with every value, then again. Returns the
        details last shown (Gate 2 repeats them), or None if neither was chosen."""
        while True:
            what = self._details(req.url, fields)
            choice = await self.control.ask(
                "Gate 1 of 2: confirm the details",
                what,
                "confirm",
                image=shot if fields == original else None,
            )
            if choice == "approve":
                return what
            if choice != "edit":
                return None
            await self._edit(fields, human)

    async def _edit(self, fields: dict[str, str], human: bool) -> None:
        editable = [k for k in fields if not is_sensitive(k, self.words)]
        opts: list[list[str]] | None
        if human:
            opts = [[] for _ in editable] if self.options.plain_edit_boxes else None
        else:
            opts = self._options(fields, editable)
        new = await self.control.form(
            "Edit the details, then Submit:",
            [(pretty(k), False) for k in editable],
            [fields[k] for k in editable],
            opts,
        )
        if new:
            fields.update(zip(editable, new, strict=False))
            self.state.given.extend(v for v in new if v)

    async def _gate2(self, what: str, image: bytes | None) -> bool:
        choice = await self.control.ask(
            "Gate 2 of 2: confirm sending",
            f"{what}\nThis cannot be undone.",
            "approve",
            image=image,
        )
        return choice == "approve"

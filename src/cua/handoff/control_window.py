"""ControlWindow: our own "Agent control" tab, the only place a human answers.

Moved from discovery.py 856-958 and replay.py 528-630: ONE class, the union of both sides' modes.
Each side's differences are explicit, set by :class:`Side` (use :func:`discovery_control` /
:func:`replay_control`): the take-over button label, the default ``who``, the "working" title, the
form note, and replay's closed-window guards (``guard_closed``). With ``guard_closed`` off the code
is discovery's (no ``is_closed`` checks, ``_front`` inside ``try``); on, it is replay's (fail closed
on a closed window or a failed ``set_content``, ``_front`` before ``try``). The ``page`` global (the
site tab, brought back to front) is the ``site_page`` constructor argument.
"""

from __future__ import annotations

import asyncio
import base64
import html
import json
from dataclasses import dataclass
from typing import Protocol


class Tab(Protocol):
    """The two Playwright pages this class touches: the control tab and the site tab."""

    async def set_content(self, html: str) -> None: ...

    def is_closed(self) -> bool: ...

    async def bring_to_front(self) -> None: ...


@dataclass(frozen=True)
class Side:
    """What differs between the discovery and replay control windows."""

    who: str  # default "In control:" label
    working_title: str  # shown once no question is open
    takeover_label: str  # the take-over panel's Done button
    form_note: str  # the form's details text
    guard_closed: bool  # replay's closed-window guards


AGENT = Side(
    who="agent",
    working_title="Agent is working",
    takeover_label="Done, hand back to agent",
    form_note="Our code enters these into the site. The agent never sees them.",
    guard_closed=False,
)
REPLAY = Side(
    who="replay",
    working_title="Replay is working",
    takeover_label="Done, hand back to replay",
    form_note="Our code enters these into the site.",
    guard_closed=True,
)

_CONTROLS = {
    "approve": "<button onclick=\"cuaReply('approve')\">Approve</button>"
    "<button onclick=\"cuaReply('reject')\">Reject</button>",
    "confirm": "<button onclick=\"cuaReply('approve')\">Approve</button>"
    "<button onclick=\"cuaReply('edit')\">Edit</button>",
    "text": '<textarea id=v rows=3 cols=60></textarea><button onclick="cuaReply(v.value)">'
    "Send</button>",
    "help": "<textarea id=v rows=4 cols=60 placeholder='Tell the agent what to do'></textarea><br>"
    "<button onclick=\"cuaReply('say:' + v.value)\">Send answer</button>"
    "<button onclick=\"cuaReply('takeover')\">Take over the site</button>"
    "<button onclick=\"cuaReply('stop')\">Stop the run</button>",
    "rescue": "<button onclick=\"cuaReply('takeover')\">Take over the site</button>"  # PLAN P2
    "<button onclick=\"cuaReply('stop')\">Stop the run</button>",
    "form": "<button onclick=\"cuaReply(JSON.stringify([...document.querySelectorAll('.f')]"
    '.map(e => e.value)))">Submit</button><button onclick="cuaReply(\'\')">Skip</button>',
    "status": "",
}
_TAKEOVER = "<button onclick=\"cuaReply('done')\">{label}</button>"

_STYLE = (
    "<style>body{font:15px sans-serif;max-width:640px;margin:24px auto;padding:0 16px}"
    "h3{margin:0 0 8px}.why{background:#fdecea;border-left:4px solid #c62828;"
    "padding:10px 12px;margin:0 0 14px;white-space:pre-line}"
    ".shot{display:block;max-width:560px;width:100%;margin:12px auto;border:1px solid #bbb}"
    "img{max-width:100%}button{margin:6px 6px 0 0;padding:8px 16px}"
    "textarea,.f{display:block;width:100%;box-sizing:border-box;padding:6px;margin:4px 0 12px}"
    ".who{color:#666;font-size:12px}</style>"
)

# (title, details, mode, image, who, rows): one question as shown
Question = tuple[str, str, str, bytes | None, str, str]


class ControlWindow:
    """Our own page: the only place a human answers. Closing it fails closed (None)."""

    def __init__(self, win: Tab, site_page: Tab, *, side: Side) -> None:
        self.win = win
        self.site_page = site_page
        self.side = side
        self._stack: list[tuple[asyncio.Future[str | None], Question]] = []  # newest on top

    def on_reply(self, value: str | None) -> None:
        """Answers the question on top. Closing the window (None) answers every one: fail closed."""
        for fut, _ in self._stack if value is None else self._stack[-1:]:
            if not fut.done():
                fut.set_result(value)

    def answer(self, mode: str, value: str) -> None:
        """Answers the newest open question of this mode, wherever it sits on the stack."""
        for fut, q in reversed(self._stack):
            if q[2] == mode and not fut.done():
                fut.set_result(value)
                return

    async def show(  # noqa: PLR0913 - the notebooks' own signature, moved unchanged
        self,
        title: str,
        details: str = "",
        mode: str = "status",
        image: bytes | None = None,
        who: str | None = None,
        rows: str = "",
    ) -> None:
        q: Question = (title, details, mode, image, who or self.side.who, rows)
        if not self.side.guard_closed:
            await self.win.set_content(self._render(q))
            return
        if self.win.is_closed():
            self.on_reply(None)
            return
        try:
            await self.win.set_content(self._render(q))
        except Exception:
            self.on_reply(None)

    async def ask(  # noqa: PLR0913 - the notebooks' own signature, moved unchanged
        self,
        title: str,
        details: str,
        mode: str,
        image: bytes | None = None,
        who: str | None = None,
        rows: str = "",
    ) -> str | None:
        """A new question supersedes the one on screen (e.g. a gate during a take-over); when it is
        answered, the earlier one comes back exactly as it was."""
        if self.side.guard_closed and self.win.is_closed():
            return None
        q: Question = (title, details, mode, image, who or self.side.who, rows)
        fut: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()
        entry = (fut, q)
        self._stack.append(entry)
        if self.side.guard_closed:  # replay: _front before try
            await self._front(q)
        try:
            if not self.side.guard_closed:  # discovery: _front inside try
                await self._front(q)
            return await fut
        finally:
            self._stack.remove(entry)
            await self._restore()

    async def form(
        self,
        title: str,
        fields: list[tuple[str, bool]],
        values: list[str] | None = None,
        options: list[list[str]] | None = None,
    ) -> list[str] | None:
        """One labelled input per field (label, masked), optionally prefilled. A dropdown row shows
        all its options. None if skipped or the window closed."""
        n = len(fields)
        rows = "".join(
            _row(i, label, masked, value, opts)
            for i, ((label, masked), value, opts) in enumerate(
                zip(fields, values or [""] * n, options or [[]] * n, strict=False)
            )
        )
        answer = await self.ask(title, self.side.form_note, "form", rows=rows)
        return json.loads(answer) if answer else None

    async def _restore(self) -> None:
        """After a question closes: the one below comes back, else the working page + site tab."""
        if self.win.is_closed():
            pass
        elif self._stack:
            await self._front(self._stack[-1][1])
        else:
            await self.show(self.side.working_title)
            if not self.side.guard_closed or not self.site_page.is_closed():
                await self.site_page.bring_to_front()

    async def _front(self, q: Question) -> None:
        if not self.side.guard_closed:
            await self.show(*q)
            await (self.site_page if q[2] == "takeover" else self.win).bring_to_front()
            return
        if self.win.is_closed():
            self.on_reply(None)
            return
        await self.show(*q)
        if self.win.is_closed():
            self.on_reply(None)
            return
        target = self.site_page if q[2] == "takeover" else self.win
        if not target.is_closed():
            await target.bring_to_front()

    def _render(self, q: Question) -> str:
        title, details, mode, image, who, rows = q
        tab = "Agent control" if mode == "status" else "▶ Agent control: your turn"
        controls = (
            _TAKEOVER.format(label=self.side.takeover_label)
            if mode == "takeover"
            else _CONTROLS[mode]
        )
        return (
            f"<title>{tab}</title>{_STYLE}"
            f"<p class=who>In control: {who}</p><h3>{html.escape(title)}</h3>"
            + (f"<div class=why>{html.escape(details)}</div>" if details else "")
            + f"{_img(image, 'shot')}{rows}<div>{controls}</div>"
        )


def discovery_control(win: Tab, site_page: Tab) -> ControlWindow:
    return ControlWindow(win, site_page, side=AGENT)


def replay_control(win: Tab, site_page: Tab) -> ControlWindow:
    return ControlWindow(win, site_page, side=REPLAY)


def _row(i: int, label: str, masked: bool, value: str, opts: list[str]) -> str:
    """A dropdown becomes a real <select> of its options; anything else a text/password box."""
    head = f"<label><b>{html.escape(label)}</b>"
    if opts:
        choices = "".join(
            f'<option{" selected" if o == value else ""}>{html.escape(o)}</option>' for o in opts
        )
        return f"{head}<select class=f>{choices}</select></label>"
    kind = "password" if masked else "text"
    return f'{head}<input class=f type={kind} value="{html.escape(value, quote=True)}"></label>'


def _img(png: bytes | None, cls: str = "") -> str:
    return (
        f'<img class="{cls}" src="data:image/png;base64,{base64.b64encode(png).decode()}">'
        if png
        else ""
    )

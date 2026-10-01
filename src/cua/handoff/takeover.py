"""The shared take-over loop pieces. Each side's own take-over stays with that side: discovery's
``take_over`` (discovery.py 530-573) and replay's ``rescue`` (replay.py 1338-1368) are built from
``SiteLock.open()``, :func:`cua.handoff.extension.handback_button` / ``watch_button``,
:func:`hand_back` and :func:`wait_held_send`.

Moved from replay.py 1285-1287 (``takeover_text``) and 1327-1335 (``hand_back``; the ``CONTROL``
global is the ``control`` parameter, the text a parameter). ``wait_held_send`` is the send-gate
wait both sides run after Done (discovery.py 554-556 with ``handback_s``, replay.py 1360-1364 with
``gate_s``): acquire with a timeout, then release; the caller turns ``False`` into its own STUCK.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Protocol


class Asker(Protocol):
    async def ask(  # noqa: PLR0913 - mirrors ControlWindow.ask
        self,
        title: str,
        details: str,
        mode: str,
        image: bytes | None = None,
        who: str | None = None,
        rows: str = "",
    ) -> str | None: ...


def takeover_text() -> str:
    return (
        "Do this step in the site tab. When you're done, click the Agent hand-back icon in the "
        "browser toolbar (pin it once from the puzzle-piece menu), or Done in the Agent control "
        "tab."
    )


async def hand_back(control: Asker, button: asyncio.Future[None], text: str) -> None:
    """Done on the toolbar button or in the take-over panel hands back. No reminders in between."""
    panel = asyncio.ensure_future(control.ask("You are in control", text, "takeover", who="human"))
    try:
        both: set[asyncio.Future[str | None] | asyncio.Future[None]] = {panel, button}
        await asyncio.wait(both, return_when=asyncio.FIRST_COMPLETED)
    finally:
        panel.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await panel


async def wait_held_send(lock: asyncio.Lock, timeout_s: float) -> bool:
    """A send the human started is still held: its gate is on screen next; wait for it. True once
    the send gate is free (acquired and released), False if it is still held after ``timeout_s``."""
    try:
        await asyncio.wait_for(lock.acquire(), timeout_s)
    except TimeoutError:
        return False
    lock.release()
    return True

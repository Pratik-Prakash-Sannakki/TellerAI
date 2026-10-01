"""Bind the control tab to the current :class:`ControlWindow`, once per tab.

A setup-cell re-run builds a new window, but ``expose_function("cuaReply", ...)`` can only be
registered once per page, and listeners stack. So the tab gets ONE ``cuaReply`` forwarder and ONE
``close`` listener, both dispatching to whichever window was bound last (``_cua_control``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from cua.handoff.control_window import ControlWindow


class ControlTab(Protocol):
    """The Playwright calls binding makes on the control tab."""

    async def expose_function(self, name: str, fn: Callable[[str | None], None]) -> None: ...

    def on(self, event: str, fn: Callable[[object], None]) -> None: ...


async def bind_control(control_page: ControlTab, control: ControlWindow) -> None:
    """Point the control tab's buttons and its close at ``control``. Re-run safe: the forwarders
    are added on the first bind only; an already exposed ``cuaReply`` is tolerated."""
    tab = control_page
    tab._cua_control = control  # type: ignore[attr-defined]
    if getattr(tab, "_cua_bound", False):
        return

    def reply(value: str | None) -> None:
        current: ControlWindow = tab._cua_control  # type: ignore[attr-defined]
        current.on_reply(value)

    try:
        await tab.expose_function("cuaReply", reply)
    except Exception as e:
        if "already registered" not in str(e):
            raise
    tab.on("close", lambda _: reply(None))
    tab._cua_bound = True  # type: ignore[attr-defined]


__all__ = ["ControlTab", "bind_control"]

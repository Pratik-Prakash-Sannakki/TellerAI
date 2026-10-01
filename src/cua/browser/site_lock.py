"""SiteLock: the site tab ignores all real input (CDP ``Input.setIgnoreInputEvents``).

Moved verbatim from discovery.py 838-853 (== replay.py 510-525). ``open()`` is the only unlock
path, and it always re-locks, even when the body raises.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Mapping
from typing import Protocol


class CdpSender(Protocol):
    """The one method of a Playwright ``CDPSession`` the lock uses."""

    async def send(self, method: str, params: Mapping[str, bool]) -> object: ...


class SiteLock:
    """The site tab ignores all real input (CDP). Lifted only around our own action or a
    take-over."""

    def __init__(self, cdp: CdpSender) -> None:
        self._cdp = cdp

    async def set(self, locked: bool) -> None:
        await self._cdp.send("Input.setIgnoreInputEvents", {"ignore": locked})

    @contextlib.asynccontextmanager
    async def open(self) -> AsyncIterator[None]:
        await self.set(False)
        try:
            yield
        finally:
            await self.set(True)

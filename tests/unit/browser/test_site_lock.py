"""SiteLock: the site tab ignores real input except inside ``open()``, which always re-locks."""

from __future__ import annotations

import pytest

from cua.browser.site_lock import SiteLock


class FakeCdp:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, bool]]] = []

    async def send(self, method: str, params: dict[str, bool]) -> None:
        self.sent.append((method, params))


@pytest.mark.asyncio
async def test_set_sends_the_cdp_ignore_input_command() -> None:
    cdp = FakeCdp()
    await SiteLock(cdp).set(True)
    assert cdp.sent == [("Input.setIgnoreInputEvents", {"ignore": True})]


@pytest.mark.asyncio
async def test_open_unlocks_then_relocks() -> None:
    cdp = FakeCdp()
    async with SiteLock(cdp).open():
        assert cdp.sent == [("Input.setIgnoreInputEvents", {"ignore": False})]
    assert cdp.sent[-1] == ("Input.setIgnoreInputEvents", {"ignore": True})


@pytest.mark.asyncio
async def test_an_exception_inside_open_still_relocks() -> None:
    cdp = FakeCdp()
    with pytest.raises(ValueError, match="boom"):
        async with SiteLock(cdp).open():
            raise ValueError("boom")
    assert [p["ignore"] for _, p in cdp.sent] == [False, True]

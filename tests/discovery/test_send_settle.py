"""D: after an approved send, act waits for the page's response before its screenshot."""
import ast
import asyncio
import contextlib
import time
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


class Page:
    """The response lands 3 polls after the gate is released."""
    def __init__(self) -> None:
        self.shots = 0

    async def screenshot(self) -> bytes:
        self.shots += 1
        return b"form" if self.shots < 4 else b"done"

    async def wait_for_timeout(self, ms) -> None:
        await asyncio.sleep(0)


async def _none():
    return []


def _act(verdict: str):
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"act", "wait_for_change"}]
    page, seen = Page(), []

    async def look():
        seen.append(await page.screenshot())
        return seen[-1]

    lock = SimpleNamespace(open=contextlib.nullcontext)
    ns = {"LOCK": lock, "SEND_GATE": asyncio.Lock(), "page": page, "take_look": look, "Look": bytes, "time": time,
          "HANDOFF": SimpleNamespace(verdict=verdict, dropdowns=[]), "read_dropdowns": _none, "screens_same": lambda a, b: a == b,
          "CFG": SimpleNamespace(settle_ms=1, send_wait_ms=5000)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)

    async def click():
        return None
    return asyncio.run(ns["act"](click)), page


def test_after_an_approved_send_the_look_shows_the_response() -> None:
    got, _ = _act("SENT: a human approved both gates.")
    assert got == b"done"


def test_no_send_means_no_extra_wait() -> None:
    got, page = _act("")
    assert got == b"form" and page.shots == 2      # before + the look


def test_landed_keeps_only_new_fixed_text() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"landed", "norm"}]
    import re
    ns = {"re": re, "Look": object, "HANDOFF": SimpleNamespace(given=["Jane Doe"], typed_texts={"42"})}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    look = lambda *texts: SimpleNamespace(text=" ".join(texts), elements=[SimpleNamespace(text=t) for t in texts])  # noqa: E731
    before = look("Bill Payment Service", "Request Loan")
    after = look("Bill Payment Complete", "Bill Payment to Jane Doe in the amount of $42.00", "13344",
                 "Request Loan")
    assert ns["landed"](before, after) == ["Bill Payment Complete"]

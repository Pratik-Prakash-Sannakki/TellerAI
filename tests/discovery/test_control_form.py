"""ControlWindow: form answers, and a newer question supersedes then restores the older one."""
import ast
import asyncio
import base64
import html
import json
from pathlib import Path

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


class FakeWin:
    def __init__(self) -> None:
        self.html, self.fronted = "", 0

    async def set_content(self, content: str) -> None:
        self.html = content

    def is_closed(self) -> bool:
        return False

    async def bring_to_front(self) -> None:
        self.fronted += 1


def _window():
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body
            if getattr(n, "name", None) in {"ControlWindow", "_img", "_row"}
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_CONTROLS")]
    win, site = FakeWin(), FakeWin()
    ns = {"asyncio": asyncio, "base64": base64, "html": html, "json": json, "page": site}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns["ControlWindow"](win), win, site


async def _settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


def test_form_returns_answers_and_masks_sensitive() -> None:
    async def run():
        cw, win, site = _window()
        task = asyncio.create_task(cw.form("Fill", [("Address", False), ("Password", True)]))
        await _settle()
        assert "type=text" in win.html and "type=password" in win.html
        cw.on_reply(json.dumps(["12 Main St", "x"]))
        assert await task == ["12 Main St", "x"]
        assert win.fronted == 1 and site.fronted == 1      # to the control tab, then back

    asyncio.run(run())


def test_gate_supersedes_takeover_then_restores_it() -> None:
    """Regression: a gate during a take-over must win, then hand the take-over back intact."""
    async def run():
        cw, win, _ = _window()
        takeover = asyncio.create_task(cw.ask("You are in control", "", "takeover"))
        await _settle()
        gate = asyncio.create_task(cw.ask("Gate 1 of 2", "", "approve"))
        await _settle()
        assert "Gate 1 of 2" in win.html                    # the gate is on screen now
        cw.on_reply("approve")                              # answers the gate, not the take-over
        assert await gate == "approve" and not takeover.done()
        await _settle()
        assert "You are in control" in win.html             # take-over is back
        cw.on_reply("done")
        assert await takeover == "done"

    asyncio.run(run())


def test_closing_the_window_fails_every_question_closed() -> None:
    async def run():
        cw, _, _ = _window()
        a = asyncio.create_task(cw.ask("a", "", "takeover"))
        b = asyncio.create_task(cw.ask("b", "", "approve"))
        await _settle()
        cw.on_reply(None)
        assert await a is None and await b is None

    asyncio.run(run())


def test_dropdown_row_lists_every_option() -> None:
    async def run():
        cw, win, _ = _window()
        task = asyncio.create_task(cw.form("Fill", [("From account", False)],
                                           options=[["13344", "14898", "15009"]]))
        await _settle()
        assert "<select class=f><option>13344</option><option>14898</option><option>15009</option>" in win.html
        assert "Options:" not in win.html
        cw.on_reply(json.dumps(["14898"]))
        assert await task == ["14898"]

    asyncio.run(run())

"""offer_control shows only the reason. (The dropdown tests moved to tests/unit/browser/test_dropdown.py.)"""
import ast
import asyncio
from pathlib import Path

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


def test_offer_control_shows_only_the_reason() -> None:
    """The red box showed the whole tool reply (URL, every OCR line) instead of the reason."""
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) == "offer_control"]
    got = []

    async def human_help(title, reason):
        got.append(reason)
    ns = {"human_help": human_help}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["offer_control"]("STUCK: not in the list: From account #\nURL: x\nText on screen:\n[1] 'a'"))
    assert got == ["not in the list: From account #"]

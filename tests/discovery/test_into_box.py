"""into_box clears the field before typing, so a retry replaces instead of doubling."""
import ast
import asyncio
from pathlib import Path

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


class FakeBox:
    def __init__(self) -> None:
        self.value, self.selected = "", False
        self.mouse, self.keyboard = self, self

    async def click(self, *_: int) -> None:
        self.selected = False

    async def press(self, key: str) -> None:
        if key == "ControlOrMeta+A":
            self.selected = True
        elif key == "Backspace" and self.selected:
            self.value, self.selected = "", False

    async def type(self, text: str) -> None:
        self.value += text


def test_typing_twice_does_not_double() -> None:
    tree = ast.parse(SRC.read_text())
    node = next(n for n in tree.body if getattr(n, "name", None) == "into_box")
    ns: dict = {"page": FakeBox(), "to_page": lambda p: p}
    exec(compile(ast.Module([node], []), str(SRC), "exec"), ns)

    async def run() -> None:
        for _ in range(2):
            for step in ns["into_box"]((10, 10), "Pratik"):
                await step()

    asyncio.run(run())
    assert ns["page"].value == "Pratik"

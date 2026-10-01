"""Dropdowns (option B): read every option and select by value, for the <select> at a point."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
NAMES = {"choose_option", "list_options", "norm", "SELECT_AT_JS"}


class Page:
    """Mimics SELECT_AT_JS against one <select> at (100, 50); nothing else on the page."""

    def __init__(self, options: list[str]) -> None:
        self.options, self.selected = options, 0

    async def evaluate(self, js: str, args):
        x, y, want = args
        if (x, y) != (100, 50):
            return None
        if want is None:
            return list(self.options)
        i = next((i for i, t in enumerate(self.options) if want.lower() in t.lower()), -1)
        if i < 0:
            return False
        self.selected = i
        return [100, 50, 0]          # centre, then its index among the page's selects

    async def wait_for_timeout(self, ms: int) -> None:
        return None


def _fns(pg: Page) -> dict:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in NAMES
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in NAMES)]

    async def take_look():
        return SimpleNamespace(text=pg.options[pg.selected], scale=1.0)
    ns = {"page": pg, "to_page": lambda p: p, "hide_secrets": lambda t: t, "take_look": take_look,
          "read_near": lambda look, point: look.text, "CFG": SimpleNamespace(settle_ms=0)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def test_lists_every_option_values_only() -> None:
    """The user's bug: two accounts, only one showed."""
    pg = Page(["14898", "124677"])
    assert asyncio.run(_fns(pg)["list_options"]((100, 50))) == ["14898", "124677"]


def test_not_a_dropdown_gives_no_options() -> None:
    assert asyncio.run(_fns(Page(["1"]))["list_options"]((5, 5))) == []


def test_selects_by_value_and_confirms_on_screen() -> None:
    pg = Page(["14898", "124677"])
    assert asyncio.run(_fns(pg)["choose_option"]((100, 50), "124677")) == 0     # the index
    assert pg.options[pg.selected] == "124677"


def test_missing_option_is_refused() -> None:
    pg = Page(["14898", "124677"])
    assert asyncio.run(_fns(pg)["choose_option"]((100, 50), "99999")) is None
    assert pg.selected == 0


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

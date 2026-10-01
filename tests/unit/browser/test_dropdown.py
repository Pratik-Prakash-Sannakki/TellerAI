"""Native dropdowns (D-B, the one non-visual exception): read every option of the <select> at a
point and set it by value (discovery: SELECT_AT_POINT_JS), or pick the Nth <select> by its
recorded index (replay: SELECT_AT_INDEX_JS). Each side's on-screen confirm is a callback."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from types import SimpleNamespace

import pytest
from playwright.async_api import Error as PlaywrightError

from cua.browser.dropdown import (
    DROPDOWNS_JS,
    DROPDOWNS_WITH_BOX_JS,
    SELECT_AT_INDEX_JS,
    SELECT_AT_POINT_JS,
    choose_option_at_index,
    choose_option_at_point,
    list_options,
    read_dropdowns,
)
from cua.config import BrowserConfig
from cua.vision.look import Look

CFG = BrowserConfig(settle_ms=0)


def _s(page: object) -> SimpleNamespace:
    """The two Session fields the choosers read."""
    return SimpleNamespace(page=page, cfg=CFG)


class PointPage:
    """Mimics SELECT_AT_POINT_JS against one <select> at (100, 50); nothing else on the page."""

    def __init__(self, options: list[str]) -> None:
        self.options, self.selected = options, 0
        self.scripts: list[str] = []

    async def evaluate(self, js: str, args: list[object]) -> object:
        self.scripts.append(js)
        x, y, want = args
        if (x, y) != (100, 50):
            return None
        if want is None:
            return list(self.options)
        assert isinstance(want, str)
        i = next((i for i, t in enumerate(self.options) if want.lower() in t.lower()), -1)
        if i < 0:
            return False
        self.selected = i
        return [100, 50, 0]  # centre, then its index among the page's selects

    async def wait_for_timeout(self, ms: int) -> None:
        return None


def _look_fn(pg: PointPage):  # type: ignore[no-untyped-def]
    async def look_fn() -> Look:
        return Look(b"", b"", (), pg.options[pg.selected])  # the url carries the "OCR" text

    return look_fn


def _shown(look: Look, point: tuple[int, int], option: str) -> bool:
    return option in look.url


def test_lists_every_option_values_only() -> None:
    """The user's bug: two accounts, only one showed."""
    pg = PointPage(["14898", "124677"])
    assert asyncio.run(list_options(pg, (100, 50), str)) == ["14898", "124677"]  # type: ignore[arg-type]
    assert pg.scripts == [SELECT_AT_POINT_JS]


def test_listed_options_go_through_hide() -> None:
    pg = PointPage(["secret-1", "x"])
    got = asyncio.run(list_options(pg, (100, 50), lambda t: t.replace("secret-1", "<pw>")))  # type: ignore[arg-type]
    assert got == ["<pw>", "x"]


def test_not_a_dropdown_gives_no_options() -> None:
    assert asyncio.run(list_options(PointPage(["1"]), (5, 5), str)) == []  # type: ignore[arg-type]


def test_selects_by_value_and_confirms_on_screen() -> None:
    pg = PointPage(["14898", "124677"])
    got = asyncio.run(
        choose_option_at_point(_s(pg), (100, 50), "124677", look_fn=_look_fn(pg), confirm=_shown)  # type: ignore[arg-type]
    )
    assert got == 0  # the index
    assert pg.options[pg.selected] == "124677"


def test_missing_option_is_refused() -> None:
    pg = PointPage(["14898", "124677"])
    got = asyncio.run(
        choose_option_at_point(_s(pg), (100, 50), "99999", look_fn=_look_fn(pg), confirm=_shown)  # type: ignore[arg-type]
    )
    assert got is None
    assert pg.selected == 0


def test_an_unconfirmed_choice_is_none() -> None:
    pg = PointPage(["14898", "124677"])
    got = asyncio.run(
        choose_option_at_point(  # type: ignore[arg-type]
            _s(pg), (100, 50), "124677", look_fn=_look_fn(pg), confirm=lambda *a: False
        )
    )
    assert got is None


FROM, TO = (540, 345, 718, 365), (805, 345, 940, 365)  # two selects on one row


def _js(x: int, y: int, want: str | None, index: int | None) -> dict[str, object]:
    """Run SELECT_AT_INDEX_JS in node against a fake page holding FROM and TO."""
    if not shutil.which("node"):
        pytest.skip("node not installed")
    page = f"""
    const mk = (r, opts) => ({{options: opts.map(t => ({{text: t}})), selectedIndex: 0,
      getBoundingClientRect: () => ({{left: r[0], top: r[1], right: r[2], bottom: r[3],
                                       width: r[2] - r[0], height: r[3] - r[1]}}),
      dispatchEvent: () => true, closest() {{ return this; }}}});
    const sel = [mk({list(FROM)}, ["13344", "15120"]), mk({list(TO)}, ["13344", "15120"])];
    const document = {{querySelectorAll: () => sel,
      elementFromPoint: (x, y) => sel.find(s => {{ const r = s.getBoundingClientRect();
        return r.left <= x && x <= r.right && r.top <= y && y <= r.bottom; }})
        ?? {{closest: () => null}}}};
    const out = ({SELECT_AT_INDEX_JS})({json.dumps([x, y, want, index])});
    console.log(JSON.stringify({{out, picked: sel.map(s => s.selectedIndex)}}));
    """
    run = subprocess.run(["node", "-e", page], capture_output=True, text=True, check=True)
    out: dict[str, object] = json.loads(run.stdout)
    return out


def test_an_index_picks_its_own_dropdown_from_a_point_nearer_the_other() -> None:
    got = _js(760, 355, "15120", 1)  # between the two, nearer FROM's right edge
    assert got["picked"] == [0, 1]
    assert got["out"][2] == "15120"  # type: ignore[index]


def test_without_an_index_the_point_decides() -> None:
    assert _js(600, 355, "15120", None)["picked"] == [1, 0]
    assert _js(900, 355, None, None)["out"] == ["13344", "15120"]


class IndexPage:
    def __init__(self) -> None:
        self.args: list[list[object]] = []

    async def evaluate(self, js: str, args: list[object]) -> object:
        assert js == SELECT_AT_INDEX_JS
        self.args.append(args)
        return [872, 355, args[2]]

    async def wait_for_timeout(self, ms: int) -> None:
        return None


@pytest.mark.asyncio
async def test_choose_at_index_sends_the_index_and_confirms_at_the_dropdown() -> None:
    page = IndexPage()
    seen: list[tuple[tuple[int, int], str]] = []

    async def look_fn() -> Look:
        return Look(b"", b"", (), "u", 2.0)

    def confirm(look: Look, point: tuple[int, int], option: str) -> bool:
        seen.append((point, option))
        return True

    ok = await choose_option_at_index(
        _s(page), (780, 355), "15120", 1, look_fn=look_fn, confirm=confirm  # type: ignore[arg-type]
    )
    assert ok is True
    assert page.args == [[780, 355, "15120", 1]]
    assert seen == [((436, 178), "15120")]


@pytest.mark.asyncio
async def test_choose_at_index_refuses_another_selected_text() -> None:
    class Wrong(IndexPage):
        async def evaluate(self, js: str, args: list[object]) -> object:
            return [1, 1, "other"]

    async def look_fn() -> Look:
        raise AssertionError("no look when the page refused")

    ok = await choose_option_at_index(
        _s(Wrong()), (1, 1), "15120", None, look_fn=look_fn, confirm=lambda *a: True  # type: ignore[arg-type]
    )
    assert ok is False


class ReadPage:
    def __init__(self, result: object = None, exc: BaseException | None = None) -> None:
        self.result, self.exc = result, exc
        self.scripts: list[str] = []

    async def evaluate(self, js: str) -> object:
        self.scripts.append(js)
        if self.exc:
            raise self.exc
        return self.result


@pytest.mark.asyncio
async def test_read_dropdowns_returns_the_page_list_with_the_given_script() -> None:
    page = ReadPage([{"value": "1"}])
    assert await read_dropdowns(page, DROPDOWNS_JS, 1.0) == [{"value": "1"}]  # type: ignore[arg-type]
    assert page.scripts == [DROPDOWNS_JS]


@pytest.mark.asyncio
async def test_read_dropdowns_is_empty_on_an_error_or_timeout() -> None:
    page = ReadPage(exc=PlaywrightError("held"))
    assert await read_dropdowns(page, DROPDOWNS_WITH_BOX_JS, 1.0) == []  # type: ignore[arg-type]
    page = ReadPage(exc=TimeoutError())
    assert await read_dropdowns(page, DROPDOWNS_JS, 1.0) == []  # type: ignore[arg-type]


def test_the_two_dropdown_scripts_differ_only_by_position_fields() -> None:
    assert "box:" in DROPDOWNS_WITH_BOX_JS
    assert "at:" in DROPDOWNS_WITH_BOX_JS
    assert "box" not in DROPDOWNS_JS

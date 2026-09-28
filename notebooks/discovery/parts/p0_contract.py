# %% [markdown]
# # Pure-visual discovery
#
# Discovery that sees the screen ONLY as a picture: screenshot -> RapidOCR -> numbered boxes ->
# deep agent -> mouse/keyboard. No DOM reads anywhere. Spec: `decisions.md` (Base, Q7-Q15),
# `discovery_architecture.md`, build plan `PLAN.md` (all decisions Q-A..Q-F made 2026-09-28).
#
# **Cell kinds**
# - `OFFLINE` cells: no browser, no network, no API key. The builder runs them with
#   `run_offline.py`; each ends in asserts and prints `OK <cell>`.
# - `BROWSER` cells: only the user runs them. They open a real, visible Chromium on ParaBank.
#
# **Setup (user):** `uv sync --group discovery`; `.env` has `PARABANK_USERNAME`,
# `PARABANK_PASSWORD`, `ANTHROPIC_API_KEY`. Run OFFLINE cells top to bottom, then the BROWSER
# cells in order, BROWSER 0 (the lock check) first.
#
# **Hard rules:** only `parabank.parasoft.com`; secrets by NAME only (`type_secret`); every click
# asks a human unless its OCR text exactly matches the config safe list (Q-B); the site tab is
# locked by the browser for the whole run and humans act ONLY through the control window (Q-A).

# %% OFFLINE 1: config + shared types (the contract every later cell builds on)
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import pathlib
from collections.abc import Coroutine
from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol, TypeVar

from cua.config import BASE, SECRETS, host_allowed, resolve_secret  # noqa: F401  (shared config)

T = TypeVar("T")


def run_sync(coro: Coroutine[object, object, T]) -> T:
    """asyncio.run() raises RuntimeError inside a Jupyter kernel, which already runs its own event
    loop. Run the coroutine to completion in a fresh worker thread (its own loop) when one is
    already running; otherwise just asyncio.run() it here."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(asyncio.run, coro).result()

HERE = pathlib.Path("notebooks/discovery") if pathlib.Path("notebooks/discovery").is_dir() else pathlib.Path(".")
FIXTURES = HERE / "fixtures"
RUNS = HERE / "runs"


@dataclass(frozen=True)
class DiscoveryConfig:
    """Every tunable and every site-specific word list. Tools read ONLY from this (no site values
    in tool code). Site lists (safe_clicks) are filled in the run cell for that site."""
    viewport: tuple[int, int] = (1280, 800)        # Q10: locked window size, CSS px == screenshot px
    scale: int = 1                                 # device_scale_factor; must stay 1 (Review focus 1)
    # Q-B + threat B2: (page name, normalised OCR text) pairs that need NO approval. Keyed by page,
    # because the same text can be a harmless menu link on one page and a submit button on another.
    safe_clicks: frozenset[tuple[str, str]] = frozenset()
    deny_words: tuple[str, ...] = ("register", "lookup", "admin")
    sensitive_words: tuple[str, ...] = ("ssn", "password", "social")
    start_pages: frozenset[str] = frozenset({"overview.htm", "index.htm"})
    scroll_px: int = 600                           # Q13: about 3/4 of the window height
    same_screen_mad: float = 1.0                   # mean abs pixel diff below this = "same screen"
    crop_pad: int = 6                              # Q14: pad around an element's own box
    point_crop: tuple[int, int] = (160, 34)        # crop size around a text-less point
    poll_ms: int = 200                             # step check poll interval
    poll_budget_ms: int = 3000                     # step check time budget
    dropdown_down_limit: int = 15                  # Q12 fallback: max down-arrow presses
    ocr_min_score: float = 0.5
    anchor_radius: int = 220                       # max px from a point to its label (rung 2)
    login_attempt_limit: int = 3                   # D69
    login_failure_texts: tuple[str, ...] = ("could not be verified", "user does not exist",
                                            "invalid username or password")
    sitemap_cap: int = 150


CFG = DiscoveryConfig()


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> Point:
        return Point((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)


@dataclass(frozen=True)
class Element:
    ref: int          # unique for the WHOLE run, never reused (Review focus 2)
    text: str
    box: Box
    score: float


@dataclass(frozen=True)
class Look:
    gen: int                          # increases on every observe/scroll
    png: bytes                        # raw screenshot (no boxes drawn)
    elements: tuple[Element, ...]

    def by_ref(self, ref: int) -> Element | None:
        return next((e for e in self.elements if e.ref == ref), None)

    def text(self) -> str:
        return " ".join(e.text for e in self.elements)


@dataclass(frozen=True)
class Anchor:
    """Rung 2 hint: a nearby label + offset from the label's box centre to the target point."""
    label: str
    ordinal: int      # 0 = first match of this label text on the screen (reading order)
    dx: int
    dy: int


@dataclass(frozen=True)
class TableRead:
    """Q8: a value read where a row (found by row_key text) crosses a column header."""
    row_key: str
    column: str


@dataclass(frozen=True)
class RungHints:
    """What discovery records so a later replay can find the target (replay itself is out of scope)."""
    text: str | None              # rung 1; None for a text-less target
    anchor: Anchor | None         # rung 2
    crop_path: str | None         # rung 3, saved picture (cut BEFORE the action, Q7b/Q14)
    table: TableRead | None       # Q8

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(raw: str) -> RungHints:
        d = json.loads(raw)
        return RungHints(
            text=d["text"],
            anchor=Anchor(**d["anchor"]) if d["anchor"] else None,
            crop_path=d["crop_path"],
            table=TableRead(**d["table"]) if d["table"] else None,
        )


ClickVerdict = Literal["deny", "ask", "safe"]
Decision = Literal["approve", "reject"]


class OcrEngine(Protocol):
    """Anything that turns a PNG into (text, box, score) triples. Real one: RapidOCR (OFFLINE 6)."""
    def __call__(self, png: bytes) -> list[tuple[str, Box, float]]: ...


class Surface(Protocol):
    """The ONLY way the agent touches the browser: pixels in, mouse/keyboard out (pure visual)."""
    @property
    def url(self) -> str: ...
    async def screenshot(self) -> bytes: ...
    async def click(self, x: int, y: int) -> None: ...
    async def type(self, text: str) -> None: ...
    async def press(self, key: str) -> None: ...
    async def wheel(self, dx: int, dy: int, x: int | None = None, y: int | None = None) -> None: ...
    async def goto(self, url: str) -> None: ...


class SiteLock(Protocol):
    """Q-A: browser-level lock on the site tab. `during()` is an async context manager that lifts the
    lock ONLY for the instant of our own action and always re-locks (try/finally)."""
    async def lock(self) -> None: ...
    async def unlock(self) -> None: ...
    def during(self): ...  # -> AbstractAsyncContextManager[None]


class ControlWindow(Protocol):
    """Q-A: the ONLY place a human acts. Humans never touch the site; our code performs the action."""
    async def approve(self, title: str, details: str, crop_png: bytes | None) -> Decision: ...
    async def ask_value(self, label: str, crop_png: bytes | None, masked: bool) -> str | None: ...
    async def ask_values(self, labels: list[str], crops: list[bytes | None]) -> list[str | None]: ...
    async def ask_text(self, question: str) -> str: ...
    async def status(self, text: str) -> None: ...


assert CFG.viewport == (1280, 800) and CFG.scale == 1
assert "parabank" not in repr(CFG).lower(), "no site values in the default config"
assert Box(0, 0, 10, 20).center == Point(5, 10)
_h = RungHints("Log In", Anchor("Password", 0, 150, 0), "crops/001.png", TableRead("20002", "Balance"))
assert RungHints.from_json(_h.to_json()) == _h
try:
    CFG.scroll_px = 1  # type: ignore[misc]
    raise AssertionError("config must be frozen")
except AttributeError:
    pass


async def _inner() -> int:
    return 42


async def _outer() -> None:
    assert run_sync(_inner()) == 42  # called from inside a running loop


async def _inner_raises() -> None:
    raise ValueError("boom")


async def _outer_raises() -> None:
    try:
        run_sync(_inner_raises())
        raise AssertionError("expected ValueError to propagate")
    except ValueError as e:
        assert str(e) == "boom"


assert run_sync(_inner()) == 42  # no loop running
run_sync(_outer())
run_sync(_outer_raises())
print("OK OFFLINE 1")


# %% OFFLINE 1b: shared test helpers (fixture screens drawn in code, so every test is reproducible)
import cv2
import numpy as np


def render_screen(labels: list[tuple[str, int, int]], rects: list[Box] = (), size: tuple[int, int] = (1280, 800),
                  scale: float = 0.8) -> bytes:
    """A white screen with black text at (x, baseline_y) and grey empty input rectangles. PNG bytes."""
    w, h = size
    img = np.full((h, w, 3), 255, np.uint8)
    for r in rects:
        cv2.rectangle(img, (r.x1, r.y1), (r.x2, r.y2), (120, 120, 120), 1)
    for text, x, y in labels:
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 2)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def png_to_bgr(png: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)


def bgr_to_png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def items(*rows: tuple[str, int, int, int, int]) -> list[tuple[str, Box, float]]:
    """Hand-made OCR output: ("Username", x1, y1, x2, y2) -> [(text, Box, 0.99)]."""
    return [(t, Box(a, b, c, d), 0.99) for t, a, b, c, d in rows]


_png = render_screen([("Username", 100, 215)], [Box(250, 195, 450, 225)])
assert png_to_bgr(_png).shape == (800, 1280, 3)
assert items(("A", 0, 0, 5, 5))[0][1] == Box(0, 0, 5, 5)
print("OK OFFLINE 1b")

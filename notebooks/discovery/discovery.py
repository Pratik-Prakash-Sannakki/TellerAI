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


# %% [markdown]
# ## Vision: OCR -> numbered boxes -> targets, anchors, table reads, crops, step checks
# Pure pixels. No DOM, no browser, no network. Every cell ends in asserts.


# %% OFFLINE 3: parse RapidOCR output into (text, Box, score) triples
import types
from collections.abc import Sequence


class OcrResultLike(Protocol):
    """What we use from rapidocr's RapidOCROutput: parallel boxes (N x 4 x 2 or None), txts, scores."""
    boxes: Sequence[Sequence[Sequence[float]]] | None
    txts: Sequence[str] | None
    scores: Sequence[float] | None


def _quad_to_box(quad: Sequence[Sequence[float]]) -> Box:
    xs = [float(p[0]) for p in quad]
    ys = [float(p[1]) for p in quad]
    return Box(int(round(min(xs))), int(round(min(ys))), int(round(max(xs))), int(round(max(ys))))


def parse_rapidocr(result: OcrResultLike, min_score: float) -> list[tuple[str, Box, float]]:
    """Quads -> axis-aligned int boxes. Drops low scores and empty text. None boxes -> []."""
    if result.boxes is None or result.txts is None or result.scores is None:
        return []
    found = []
    for quad, txt, score in zip(result.boxes, result.txts, result.scores):
        text = str(txt).strip()
        if text and float(score) >= min_score:
            found.append((text, _quad_to_box(quad), float(score)))
    return found


def load_ocr_fixture(name: str) -> list[tuple[str, Box, float]]:
    raw = json.loads((FIXTURES / "ocr" / f"{name}.json").read_text())
    result = types.SimpleNamespace(boxes=raw["boxes"], txts=raw["txts"], scores=raw["scores"])
    return parse_rapidocr(result, CFG.ocr_min_score)


_login = load_ocr_fixture("login")
assert [t for t, _, _ in _login] == ["Username", "Password", "Log In"], _login
assert _login[0][1] == Box(100, 200, 190, 222)
assert load_ocr_fixture("empty") == []
assert len(load_ocr_fixture("accounts")) == 1 + 3 + 9
print("OK OFFLINE 3")


# %% OFFLINE 4: number elements in reading order with run-wide refs
class RefCounter:
    """Run-wide ref numbers: start at 1, never reused (Review focus 2)."""

    def __init__(self) -> None:
        self._last = 0

    def next(self) -> int:
        self._last += 1
        return self._last


def _same_row(a: Box, b: Box) -> bool:
    """Vertical overlap >= 50% of the smaller height."""
    overlap = min(a.y2, b.y2) - max(a.y1, b.y1)
    smaller = max(1, min(a.y2 - a.y1, b.y2 - b.y1))
    return overlap >= 0.5 * smaller


def group_rows(boxes: list[Box]) -> list[list[int]]:
    """Indices of `boxes` grouped into rows: rows top to bottom, left to right within a row."""
    order = sorted(range(len(boxes)), key=lambda i: (boxes[i].center.y, boxes[i].x1))
    rows: list[list[int]] = []
    for i in order:
        if rows and any(_same_row(boxes[i], boxes[j]) for j in rows[-1]):
            rows[-1].append(i)
        else:
            rows.append([i])
    return [sorted(r, key=lambda i: boxes[i].x1) for r in rows]


def number(found: list[tuple[str, Box, float]], counter: RefCounter) -> tuple[Element, ...]:
    rows = group_rows([b for _, b, _ in found])
    ordered = [found[i] for row in rows for i in row]
    return tuple(Element(counter.next(), t, b, s) for t, b, s in ordered)


_c = RefCounter()
_els = number(list(reversed(_login)), _c)
assert [e.text for e in _els] == ["Username", "Password", "Log In"]
assert [e.ref for e in _els] == [1, 2, 3]
_els2 = number(_login, _c)
assert [e.ref for e in _els2] == [4, 5, 6], "refs are never reused"
_row = number(items(("B", 300, 102, 340, 120), ("A", 100, 100, 150, 118), ("C", 100, 140, 150, 160)),
              RefCounter())
assert [e.text for e in _row] == ["A", "B", "C"], "same row left to right, then next row"
print("OK OFFLINE 4")


# %% OFFLINE 5: draw numbered boxes + the text list the model sees
RED = (0, 0, 255)  # BGR


def draw_numbered(png: bytes, elements: tuple[Element, ...]) -> bytes:
    """Red box + red ref number above each element. Same size as the input."""
    img = png_to_bgr(png)
    for e in elements:
        cv2.rectangle(img, (e.box.x1, e.box.y1), (e.box.x2, e.box.y2), RED, 2)
        label_y = e.box.y1 - 4 if e.box.y1 >= 16 else e.box.y2 + 14
        cv2.putText(img, str(e.ref), (e.box.x1, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, RED, 1)
    return bgr_to_png(img)


def format_elements(elements: tuple[Element, ...]) -> str:
    if not elements:
        return "(no text found on screen)"
    return "\n".join(f"[{e.ref}] {e.text!r}" for e in elements)


_png5 = render_screen([("Username", 100, 215)])
_els5 = number(items(("Username", 100, 198, 220, 222)), RefCounter())
_out5 = draw_numbered(_png5, _els5)
_img5 = png_to_bgr(_out5)
assert _img5.shape == png_to_bgr(_png5).shape
for _yy, _xx in ((198, 160), (222, 160), (210, 100), (210, 220)):
    _b, _g, _r = (int(v) for v in _img5[_yy, _xx])
    assert _r > 200 and _g < 60 and _b < 60, ("red edge", _yy, _xx, _b, _g, _r)
_fe = (Element(7, "Transfer", Box(0, 0, 1, 1), 0.9), Element(8, "Log In", Box(0, 0, 1, 1), 0.9))
assert format_elements(_fe) == "[7] 'Transfer'\n[8] 'Log In'"
assert format_elements(()) == "(no text found on screen)"
print("OK OFFLINE 5")


# %% OFFLINE 6: real RapidOCR smoke test (local models, no network) + fuzzy_find
import difflib
import time

_RAPID = globals().get("_RAPID")  # ONE shared RapidOCR engine, kept across cell re-runs


def _rapid_engine():  # -> rapidocr.RapidOCR
    global _RAPID
    if _RAPID is None:
        from rapidocr import RapidOCR

        _RAPID = RapidOCR()
    return _RAPID


def make_ocr_engine(min_score: float = CFG.ocr_min_score) -> OcrEngine:
    def ocr(png: bytes) -> list[tuple[str, Box, float]]:
        return parse_rapidocr(_rapid_engine()(png_to_bgr(png)), min_score)

    return ocr


def fuzzy_find(elements: Sequence[Element], text: str, cutoff: float = 0.8) -> Element | None:
    """Best difflib match (casefolded) at or above `cutoff`; the first one wins a tie."""
    want = text.casefold()
    best, best_ratio = None, cutoff
    for e in elements:
        ratio = difflib.SequenceMatcher(None, e.text.casefold(), want).ratio()
        if ratio > best_ratio or (best is None and ratio >= cutoff):
            best, best_ratio = e, ratio
    return best


_synth = render_screen([("Username", 100, 215), ("Password", 100, 255), ("Log In", 210, 295)],
                       [Box(250, 195, 450, 225), Box(250, 235, 450, 265)])
(FIXTURES / "png").mkdir(parents=True, exist_ok=True)
(FIXTURES / "png" / "login_synth.png").write_bytes(_synth)
OCR = make_ocr_engine()
OCR(_synth)  # warm-up (model load)
_t0 = time.time()
_found6 = OCR(_synth)
print(f"RapidOCR time: {time.time() - _t0:.2f}s, found {[t for t, _, _ in _found6]}")
_els6 = number(_found6, RefCounter())
for _want in ("Username", "Password", "Log In"):
    assert fuzzy_find(_els6, _want) is not None, (_want, _found6)
assert fuzzy_find(_els6, "Transfer Funds") is None
assert fuzzy_find((Element(1, "Log ln", Box(0, 0, 1, 1), 0.9),), "log in").text == "Log ln"
print("OK OFFLINE 6")


# %% OFFLINE 7: resolve a ref or a point to a click point (refuse stale / ambiguous / off-screen)
def resolve_target(look: Look, ref: int | None, x: int | None, y: int | None,
                   cfg: DiscoveryConfig) -> Point | str:
    """A ref -> its box centre; a point -> itself. Any doubt -> a REFUSED/STALE message."""
    has_point = x is not None or y is not None
    if ref is not None and has_point:
        return "REFUSED: give a number OR a point, not both"
    if ref is None and not has_point:
        return "REFUSED: give a number or a point"
    if ref is not None:
        el = look.by_ref(ref)
        if el is None:
            return f"STALE: [{ref}] is not on the latest screen. Call observe and use the new numbers."
        return el.box.center
    if x is None or y is None:
        return "REFUSED: give both x and y for a point"
    w, h = cfg.viewport
    if not (0 <= x < w and 0 <= y < h):
        return f"REFUSED: point ({x}, {y}) is outside the {w}x{h} window"
    return Point(x, y)


_look7 = Look(3, b"", number(_login, RefCounter()))
assert resolve_target(_look7, 1, None, None, CFG) == Box(100, 200, 190, 222).center
assert resolve_target(_look7, None, 300, 211, CFG) == Point(300, 211)
assert resolve_target(_look7, 1, 5, 5, CFG) == "REFUSED: give a number OR a point, not both"
assert resolve_target(_look7, None, None, None, CFG) == "REFUSED: give a number or a point"
assert resolve_target(_look7, 99, None, None, CFG) == (
    "STALE: [99] is not on the latest screen. Call observe and use the new numbers.")
assert resolve_target(_look7, None, 5, None, CFG).startswith("REFUSED")
assert resolve_target(_look7, None, 1280, 10, CFG) == "REFUSED: point (1280, 10) is outside the 1280x800 window"
assert resolve_target(_look7, None, 10, -1, CFG) == "REFUSED: point (10, -1) is outside the 1280x800 window"
print("OK OFFLINE 7")


# %% OFFLINE 9: nearest label anchor for a text-less point (rung 2)
BAND = 15  # px: how far off the point's own row/column a label may sit


def _dist(a: Point, b: Point) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def _contains(box: Box, p: Point) -> bool:
    return box.x1 <= p.x <= box.x2 and box.y1 <= p.y <= box.y2


def _nearest(cands: list[Element], point: Point, radius: int) -> Element | None:
    near = [e for e in cands if _dist(e.box.center, point) <= radius]
    return min(near, key=lambda e: _dist(e.box.center, point), default=None)


def nearest_anchor(elements: Sequence[Element], point: Point, cfg: DiscoveryConfig) -> Anchor | None:
    """Rung 2: a label left of the point on its row, else directly above. `elements` in reading order."""
    others = [e for e in elements if not _contains(e.box, point)]
    left = [e for e in others if e.box.x2 <= point.x
            and min(e.box.y2, point.y + BAND) > max(e.box.y1, point.y - BAND)]
    above = [e for e in others if e.box.y2 <= point.y
             and min(e.box.x2, point.x + BAND) > max(e.box.x1, point.x - BAND)]
    label = _nearest(left, point, cfg.anchor_radius) or _nearest(above, point, cfg.anchor_radius)
    if label is None:
        return None
    same = [e for e in elements if e.text.casefold() == label.text.casefold()]
    c = label.box.center
    return Anchor(label.text, same.index(label), point.x - c.x, point.y - c.y)


assert nearest_anchor(_look7.elements, Point(295, 211), CFG) == Anchor("Username", 0, 150, 0)
_amounts = number(load_ocr_fixture("two_amounts"), RefCounter())
assert nearest_anchor(_amounts, Point(285, 410), CFG) == Anchor("Amount", 1, 150, 0)
assert nearest_anchor(_amounts, Point(285, 210), CFG) == Anchor("Amount", 0, 150, 0)
assert nearest_anchor(_amounts, Point(135, 460), CFG) == Anchor("Amount", 1, 0, 50), "label above"
assert nearest_anchor(_amounts, Point(1200, 700), CFG) is None
assert nearest_anchor(_look7.elements, Point(145, 211), CFG) is None, "a box never anchors to itself"
print("OK OFFLINE 9")


# %% OFFLINE 10: read a table cell as (row key, column header) (Q8)
def _x_overlap(a: Box, b: Box) -> int:
    return max(0, min(a.x2, b.x2) - max(a.x1, b.x1))


def _column_of(headers: list[Element], box: Box) -> Element | None:
    """The header overlapping `box` most. None if < 30% of the box width or a tie."""
    scored = sorted(((_x_overlap(h.box, box), i) for i, h in enumerate(headers)), reverse=True)
    if not scored or scored[0][0] < 0.3 * max(1, box.x2 - box.x1):
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None
    return headers[scored[0][1]]


def _header_like(row: list[Element], target_row: list[Element]) -> tuple[int, bool]:
    """(how many cells line up with the target row's columns, are they all digit-free words)."""
    cols = [e for e in row if any(_x_overlap(e.box, t.box) for t in target_row)]
    return len(cols), len(cols) >= 2 and all(not any(ch.isdigit() for ch in e.text) for e in cols)


def _find_header(rows: list[list[Element]], idx: int) -> list[Element] | None:
    """Walk up from the target row inside the table block; the first digit-free row is the header.
    A row that is not table-shaped (< 2 aligned cells) ends the table: no header."""
    for row in reversed(rows[:idx]):
        count, wordy = _header_like(row, rows[idx])
        if count < 2:
            return None
        if wordy:
            return [e for e in row if any(_x_overlap(e.box, t.box) for t in rows[idx])]
    return None


def infer_table_cell(elements: Sequence[Element], ref: int) -> TableRead | None:
    """Q8: the target cell as (row key, column header). Any doubt -> None (a human is asked)."""
    els = list(elements)
    rows = [[els[i] for i in r] for r in group_rows([e.box for e in els])]
    idx = next((i for i, r in enumerate(rows) if any(e.ref == ref for e in r)), None)
    if idx is None or _header_like(rows[idx], rows[idx])[1]:
        return None
    headers = _find_header(rows, idx)
    target = next(e for e in rows[idx] if e.ref == ref)
    column = _column_of(headers, target.box) if headers else None
    if column is None:
        return None
    key = next((e for e in rows[idx] if _column_of(headers, e.box) is not column), None)
    return TableRead(key.text, column.text) if key else None


def _ref_of(els, text, x1):
    return next(e.ref for e in els if e.text == text and e.box.x1 == x1)


_acc = number(load_ocr_fixture("accounts"), RefCounter())
assert infer_table_cell(_acc, _ref_of(_acc, "$100.00", 300)) == TableRead("20002", "Balance")
assert infer_table_cell(_acc, _ref_of(_acc, "$75.25", 500)) == TableRead("20013", "Available")
_mov = number(load_ocr_fixture("accounts_moved"), RefCounter())
assert infer_table_cell(_mov, _ref_of(_mov, "$100.00", 100)) == TableRead("20002", "Balance")
_mrg = number(load_ocr_fixture("accounts_merged_header"), RefCounter())
assert infer_table_cell(_mrg, _ref_of(_mrg, "$100.00", 300)) is None, "merged header -> refuse"
assert infer_table_cell(_acc, _ref_of(_acc, "Balance", 300)) is None, "a header is not a value"
_lone = number(items(("Balance", 100, 200, 170, 220), ("$100.00", 200, 200, 270, 220)), RefCounter())
assert infer_table_cell(_lone, _ref_of(_lone, "$100.00", 200)) is None
assert infer_table_cell(_acc, 9999) is None
_amb = number(items(("Account", 100, 150, 175, 170), ("Balance", 180, 150, 255, 170),
                    ("20002", 100, 190, 150, 210), ("$1.00", 160, 190, 195, 210)), RefCounter())
assert infer_table_cell(_amb, _ref_of(_amb, "$1.00", 160)) is None, "tied columns -> refuse"
print("OK OFFLINE 10")


# %% OFFLINE 11: rung-3 crop, with every neighbour's text blanked (Q14)
def _clamp_box(x1: int, y1: int, x2: int, y2: int, cfg: DiscoveryConfig) -> Box:
    w, h = cfg.viewport
    return Box(max(0, x1), max(0, y1), min(w, x2), min(h, y2))


def crop_box_for(target: Element | Point, cfg: DiscoveryConfig) -> Box:
    """Element: its box + crop_pad. Point: a point_crop-sized box centred on it. Clamped."""
    if isinstance(target, Element):
        b, p = target.box, cfg.crop_pad
        return _clamp_box(b.x1 - p, b.y1 - p, b.x2 + p, b.y2 + p, cfg)
    cw, ch = cfg.point_crop
    x1, y1 = target.x - cw // 2, target.y - ch // 2
    return _clamp_box(x1, y1, x1 + cw, y1 + ch, cfg)


def cut_crop(png: bytes, box: Box, elements: Sequence[Element], keep_ref: int | None) -> bytes:
    """Q14: cut `box` and paint every OTHER element's box (inside the crop) with the crop's median
    colour, so a neighbour's text (an account number, say) never becomes part of the picture."""
    crop = png_to_bgr(png)[box.y1:box.y2, box.x1:box.x2].copy()
    fill = np.median(crop.reshape(-1, 3), axis=0).astype(np.uint8)
    for e in elements:
        if e.ref == keep_ref:
            continue
        x1, y1 = max(e.box.x1, box.x1) - box.x1, max(e.box.y1, box.y1) - box.y1
        x2, y2 = min(e.box.x2 + 1, box.x2) - box.x1, min(e.box.y2 + 1, box.y2) - box.y1
        if x2 > x1 and y2 > y1:
            crop[y1:y2, x1:x2] = fill
    return bgr_to_png(crop)


_e11 = Element(1, "Log In", Box(210, 280, 270, 302), 0.9)
assert crop_box_for(_e11, CFG) == Box(204, 274, 276, 308)
assert crop_box_for(Point(350, 210), CFG) == Box(270, 193, 430, 227)
assert crop_box_for(Point(5, 795), CFG) == Box(0, 778, 85, 800), "clamped to the window"
_png11 = render_screen([("Name", 100, 215), ("20002", 380, 216)], [Box(250, 195, 450, 225)], scale=0.6)
_els11 = number(OCR(_png11), RefCounter())
_acct = fuzzy_find(_els11, "20002")
assert _acct is not None, _els11
_cb = crop_box_for(Point(340, 210), CFG)
_crop = cut_crop(_png11, _cb, _els11, keep_ref=None)
_ci = png_to_bgr(_crop)
assert _ci.shape == (_cb.y2 - _cb.y1, _cb.x2 - _cb.x1, 3)
_ix1, _iy1 = max(_acct.box.x1, _cb.x1) - _cb.x1, max(_acct.box.y1, _cb.y1) - _cb.y1
_ix2, _iy2 = min(_acct.box.x2, _cb.x2) - _cb.x1, min(_acct.box.y2, _cb.y2) - _cb.y1
assert _ci[_iy1:_iy2, _ix1:_ix2].std() < 1, "blanked region is flat"
_raw_crop = png_to_bgr(_png11)[_cb.y1:_cb.y2, _cb.x1:_cb.x2]
assert any(ch.isdigit() for t, _, _ in OCR(bgr_to_png(_raw_crop)) for ch in t), "control: digits before"
assert not any(ch.isdigit() for t, _, _ in OCR(_crop) for ch in t), "Q14: no neighbour digits"
_kept = cut_crop(_png11, crop_box_for(_acct, CFG), _els11, keep_ref=_acct.ref)
assert any(ch.isdigit() for t, _, _ in OCR(_kept) for ch in t), "own text is kept"
print("OK OFFLINE 11")


# %% OFFLINE 12: step checks (typed text, secret leaks, same screen, polling)
from collections.abc import Awaitable, Callable

SECRET_DOTS = frozenset("•●*·")


def read_box_text(elements: Sequence[Element], box: Box) -> str:
    return " ".join(e.text for e in elements if _contains(box, e.box.center))


def _norm(s: str) -> str:
    return " ".join(s.casefold().split())


def typed_ok(read: str, expected: str, secret: bool) -> bool:
    """Secret: masking dots only. Plain: the expected text appears in what OCR read back."""
    if secret:
        has_dot = any(ch in SECRET_DOTS for ch in read)
        return has_dot and not any(ch.isalnum() for ch in read if ch not in SECRET_DOTS)
    return _norm(expected) in _norm(read)


def secret_leaked(read: str, value: str) -> bool:
    squash = "".join(value.casefold().split())
    return bool(squash) and squash in "".join(read.casefold().split())


def screens_same(a: bytes, b: bytes, cfg: DiscoveryConfig) -> bool:
    ia, ib = png_to_bgr(a), png_to_bgr(b)
    if ia.shape != ib.shape:
        return False
    return float(np.mean(cv2.absdiff(ia, ib))) < cfg.same_screen_mad


async def poll_until(check: Callable[[], Awaitable[bool]], budget_ms: int, interval_ms: int,
                     sleep: Callable[[float], Awaitable[None]] = asyncio.sleep) -> bool:
    """Try at t=0, then every interval, while the next try still fits in the budget."""
    waited = 0
    while True:
        if await check():
            return True
        if waited + interval_ms > budget_ms:
            return False
        await sleep(interval_ms / 1000)
        waited += interval_ms


assert read_box_text(_look7.elements, Box(90, 190, 300, 270)) == "Username Password"
assert read_box_text(_look7.elements, Box(0, 0, 10, 10)) == ""
assert typed_ok("••••••", "hunter2", secret=True)
assert typed_ok("*** *", "x", secret=True)
assert not typed_ok("", "x", secret=True)
assert not typed_ok("hunter2", "hunter2", secret=True), "plain text in a secret box is not ok"
assert not typed_ok("••a", "x", secret=True)
assert typed_ok("Amount  500 ", "500", secret=False)
assert typed_ok("JOHN   smith", "john smith", secret=False)
assert not typed_ok("50", "500", secret=False)
assert secret_leaked("Pass word: HUNTER 2", "hunter2")
assert not secret_leaked("••••", "hunter2")
assert not secret_leaked("anything", "")
_a = png_to_bgr(_synth)
_b = _a.copy()
_b[200:220, 460] = 0  # a blinking caret
_d = _a.copy()
_d[100:400, 100:500] = 0  # a real change
assert screens_same(_synth, bgr_to_png(_b), CFG)
assert not screens_same(_synth, bgr_to_png(_d), CFG)
assert not screens_same(_synth, render_screen([], size=(640, 400)), CFG)

_sleeps: list[float] = []


async def _fake_sleep(s: float) -> None:
    _sleeps.append(s)


def _checker(true_on: int):
    calls = []

    async def check() -> bool:
        calls.append(1)
        return len(calls) >= true_on
    return check, calls


_chk, _calls = _checker(1)
assert run_sync(poll_until(_chk, 1000, 200, sleep=_fake_sleep)) and _sleeps == [] and len(_calls) == 1
_chk, _calls = _checker(3)
assert run_sync(poll_until(_chk, 1000, 200, sleep=_fake_sleep)) and _sleeps == [0.2, 0.2]
_sleeps.clear()
_chk, _calls = _checker(99)
assert not run_sync(poll_until(_chk, 1000, 200, sleep=_fake_sleep))
assert _sleeps == [0.2] * 5 and len(_calls) == 6, "t=0 then every 200ms up to the budget"
print("OK OFFLINE 12")


# %% OFFLINE 2: host gate (cua.config.host_allowed, used as is; no localhost exception, Q-C)
assert host_allowed("https://parabank.parasoft.com/parabank/index.htm")
for _bad in ("http://127.0.0.1:8000/x", "http://localhost/", "file:///etc/passwd",
             "https://evil.com", "https://parabank.parasoft.com.evil.com"):
    assert not host_allowed(_bad), _bad
print("OK OFFLINE 2")


# %% OFFLINE 2b: sitemap (Task 1b). Found -> page list as agent context. Not found -> carry on.
import dataclasses
import re
from collections.abc import Callable, Iterable
from types import SimpleNamespace
from urllib.parse import urlparse


def fetch_sitemap_urls(site: str, tree_fn: Callable[[str], object] | None = None) -> list[str]:
    """Every allowed page URL from `site`'s sitemap, in order, de-duplicated. Any failure -> []."""
    if not host_allowed(site):
        return []
    try:
        if tree_fn is None:
            from usp.tree import sitemap_tree_for_homepage

            tree_fn = sitemap_tree_for_homepage
        urls: list[str] = []
        for page in tree_fn(site).all_pages():
            if host_allowed(page.url) and page.url not in urls:
                urls.append(page.url)
        return urls
    except Exception as exc:  # any failure = "no sitemap", never a crash
        print(f"sitemap: skipped ({type(exc).__name__})")
        return []


def sitemap_paths(urls: list[str], cfg: DiscoveryConfig) -> list[str]:
    """Path only (no host, no query), de-duplicated, deny-word paths removed."""
    deny = [w.casefold() for w in cfg.deny_words]
    paths: list[str] = []
    for url in urls:
        path = urlparse(url).path or "/"
        if path not in paths and not any(w in path.casefold() for w in deny):
            paths.append(path)
    return paths


def sitemap_context(urls: list[str], cfg: DiscoveryConfig) -> str:
    """Agent context text listing the sitemap's paths, capped at cfg.sitemap_cap."""
    paths = sitemap_paths(urls, cfg)
    if not paths:
        return ""
    lines = paths[: cfg.sitemap_cap]
    if len(paths) > cfg.sitemap_cap:
        lines.append(f"... and {len(paths) - cfg.sitemap_cap} more")
    return "Pages listed in this site's sitemap (you may open_path any of them):\n" + "\n".join(lines)


class _FakeTree:
    def __init__(self, urls: Iterable[str]) -> None:
        self._urls = list(urls)

    def all_pages(self) -> Iterable[SimpleNamespace]:
        return (SimpleNamespace(url=u) for u in self._urls)


_SITE = "https://parabank.parasoft.com/parabank/"
_sitemap_calls: list[str] = []


def _fake_tree_fn(site: str) -> _FakeTree:
    _sitemap_calls.append(site)
    return _FakeTree([_SITE + "index.htm", _SITE + "about.htm?x=1", "https://evil.com/steal.htm",
                      _SITE + "index.htm", _SITE + "register.htm", _SITE + "about.htm"])


def _raising_tree_fn(site: str) -> _FakeTree:
    raise ConnectionError("no sitemap")


_urls = fetch_sitemap_urls(_SITE, tree_fn=_fake_tree_fn)
assert _urls == [_SITE + "index.htm", _SITE + "about.htm?x=1", _SITE + "register.htm", _SITE + "about.htm"]
assert _sitemap_calls == [_SITE]
assert sitemap_paths(_urls, CFG) == ["/parabank/index.htm", "/parabank/about.htm"]
_ctx = sitemap_context(_urls, CFG)
assert _ctx.startswith("Pages listed in this site's sitemap (you may open_path any of them):\n")
assert _ctx.splitlines()[1:] == ["/parabank/index.htm", "/parabank/about.htm"]
assert "https://" not in _ctx and "register" not in _ctx and "evil" not in _ctx
assert fetch_sitemap_urls(_SITE, tree_fn=_raising_tree_fn) == []
_sitemap_calls.clear()
assert fetch_sitemap_urls("https://evil.com/", tree_fn=_fake_tree_fn) == []
assert _sitemap_calls == [], "a disallowed site must never be fetched"
assert sitemap_context([], CFG) == ""
_many = [f"{_SITE}p{i}.htm" for i in range(5)]
_cut = sitemap_context(_many, dataclasses.replace(CFG, sitemap_cap=3)).splitlines()
assert _cut[1:] == ["/parabank/p0.htm", "/parabank/p1.htm", "/parabank/p2.htm", "... and 2 more"]
assert "https://" not in "\n".join(_cut)
print("OK OFFLINE 2b")


# %% OFFLINE 8: click gate (Q-B: deny by default; "safe" only on an exact config-list match)
_TRAILING_PUNCT = ".:!?"


def normalise(text: str | None) -> str:
    """casefold, collapse whitespace, strip, strip trailing . : ! ?"""
    if not text:
        return ""
    return " ".join(text.casefold().split()).rstrip(_TRAILING_PUNCT).strip()


def classify_click(text: str | None, cfg: DiscoveryConfig, page: str, dup_count: int) -> ClickVerdict:
    """Q-B deny by default, keyed by page (threat B2).
    deny: any deny word in the text (word boundary). safe: ONLY an exact (page, text) match in
    cfg.safe_clicks AND the text appears exactly once on the screen (dup_count == 1), so a safe
    menu link can't be confused with a same-text button. Everything else, text-less included: ask."""
    norm = normalise(text)
    if not norm:
        return "ask"
    for word in cfg.deny_words:
        if re.search(rf"\b{re.escape(normalise(word))}\b", norm):
            return "deny"
    safe = {(p.casefold(), normalise(t)) for p, t in cfg.safe_clicks}
    if dup_count == 1 and (page.casefold(), norm) in safe:
        return "safe"
    return "ask"


assert normalise("  Log   In:  ") == "log in"
assert normalise(None) == ""
assert normalise("OK!?") == "ok"
_cfg8 = dataclasses.replace(CFG, safe_clicks=frozenset({("index.htm", "Log In"),
                                                        ("overview.htm", "Find Transactions")}))
_cases8: dict[str | None, ClickVerdict] = {
    "Log In": "safe", "log in ": "safe", "Log In:": "safe", "Log In Now": "ask", "Transfer": "ask",
    "Confirm": "ask", None: "ask", "": "ask", "Register": "deny", "Log ln": "ask",
}
for _t, _want in _cases8.items():
    assert classify_click(_t, _cfg8, "index.htm", 1) == _want, (_t, _want)
assert classify_click("Log In", _cfg8, "transfer.htm", 1) == "ask", "B2: safe only on its own page"
assert classify_click("Log In", _cfg8, "INDEX.HTM", 1) == "safe", "page names compare casefolded"
assert classify_click("Log In", _cfg8, "index.htm", 2) == "ask", "B2: the same text twice on screen asks"
assert classify_click("Log In", _cfg8, "index.htm", 0) == "ask", "dup_count 0 is never safe"
assert classify_click("Find Transactions", _cfg8, "overview.htm", 1) == "safe"
assert classify_click("Log In", CFG, "index.htm", 1) == "ask", "empty default list: nothing is safe"
_both = dataclasses.replace(CFG, safe_clicks=frozenset({("index.htm", "Register")}))
assert classify_click("Register", _both, "index.htm", 1) == "deny", "a deny word beats a safe entry"
assert classify_click("Registered", CFG, "index.htm", 1) == "ask", "word boundary"
print("OK OFFLINE 8")


# %% OFFLINE 13: dropdown by keyboard (Q12). Type + Enter, check by OCR; fallback: ArrowDown steps.
from collections.abc import Awaitable


async def choose_option(surface: Surface, point: Point, option: str,
                        read_text: Callable[[], Awaitable[str]], cfg: DiscoveryConfig) -> str:
    """Pick `option` in the dropdown at `point`. "OK" when OCR shows it, else "ASK_HUMAN"."""
    want = normalise(option)
    await surface.click(point.x, point.y)
    await surface.type(option)
    await surface.press("Enter")
    if want in normalise(await read_text()):
        return "OK"
    for _ in range(cfg.dropdown_down_limit):
        await surface.click(point.x, point.y)
        await surface.press("ArrowDown")
        await surface.press("Enter")
        if want in normalise(await read_text()):
            return "OK"
    return "ASK_HUMAN"


class FakeDropdown:
    """A <select> seen only through pixels: typing a matching prefix jumps to it (if `typeable`);
    ArrowDown moves one option down the list. Records every call."""

    def __init__(self, options: list[str], typeable: bool = True) -> None:
        self.options, self.typeable, self.index, self.calls = options, typeable, 0, []

    @property
    def url(self) -> str:
        return "https://parabank.parasoft.com/parabank/fake.htm"

    async def screenshot(self) -> bytes:
        return b""

    async def click(self, x: int, y: int) -> None:
        self.calls.append(("click", x, y))

    async def type(self, text: str) -> None:
        self.calls.append(("type", text))
        hit = [i for i, o in enumerate(self.options) if o.casefold().startswith(text.casefold())]
        if self.typeable and hit:
            self.index = hit[0]

    async def press(self, key: str) -> None:
        self.calls.append(("press", key))
        if key == "ArrowDown":
            self.index = min(self.index + 1, len(self.options) - 1)

    async def wheel(self, dx: int, dy: int, x: int | None = None, y: int | None = None) -> None:
        self.calls.append(("wheel", dx, dy))

    async def goto(self, url: str) -> None:
        self.calls.append(("goto", url))

    async def shown(self) -> str:
        return self.options[self.index]


_opts = ["12345", "12456", "13344", "13511", "14000"]
_p = Point(300, 200)
_d1 = FakeDropdown(_opts)
assert run_sync(choose_option(_d1, _p, "13344", _d1.shown, CFG)) == "OK"
assert _d1.calls == [("click", 300, 200), ("type", "13344"), ("press", "Enter")]
_d2 = FakeDropdown(_opts, typeable=False)
assert run_sync(choose_option(_d2, _p, "13511", _d2.shown, CFG)) == "OK"
assert [c for c in _d2.calls if c == ("press", "ArrowDown")] == [("press", "ArrowDown")] * 3
_d3 = FakeDropdown(_opts, typeable=False)
assert run_sync(choose_option(_d3, _p, "99999", _d3.shown, CFG)) == "ASK_HUMAN"
assert _d3.calls.count(("press", "ArrowDown")) == CFG.dropdown_down_limit
_d4 = FakeDropdown(_opts, typeable=False)
assert run_sync(choose_option(_d4, _p, "99999", _d4.shown, dataclasses.replace(CFG, dropdown_down_limit=2))) == "ASK_HUMAN"
assert _d4.calls.count(("press", "ArrowDown")) == 2
print("OK OFFLINE 13")


# %% OFFLINE 14: event log (events.jsonl + shots/ + crops/ + run.json). Secrets by NAME only.
import tempfile
import time


@dataclass(frozen=True)
class EventExtras:
    """Optional parts of one event (kept together so record() stays within 6 parameters)."""
    shot_png: bytes | None = None
    crop_png: bytes | None = None
    hints: RungHints | None = None      # crop_path is filled in by record() from the crop it saves
    human_entry: bool = False
    extra: dict[str, object] | None = None


class EventLog:
    """One run's log: run_dir/events.jsonl, run_dir/shots/NNN.png, run_dir/crops/NNN.png."""

    def __init__(self, run_dir: pathlib.Path) -> None:
        self.run_dir = run_dir
        self.path = run_dir / "events.jsonl"
        (run_dir / "shots").mkdir(parents=True, exist_ok=True)
        (run_dir / "crops").mkdir(parents=True, exist_ok=True)
        self.step = 0

    def _save(self, folder: str, png: bytes | None) -> str | None:
        if png is None:
            return None
        rel = f"{folder}/{self.step:03d}.png"
        (self.run_dir / rel).write_bytes(png)
        return rel

    def record(self, tool: str, args: dict[str, object], result: str,
               extras: EventExtras | None = None) -> int:
        """Append one event; return its 1-based step number. The saved crop's path is written
        into hints.crop_path (M2), so replay's rung-3 picture always points at a real file."""
        if "value_secret" in args:
            raise ValueError("refusing to log a secret value; log {'secret_name': ...} instead")
        x = extras or EventExtras()
        self.step += 1
        crop = self._save("crops", x.crop_png)
        hints = dataclasses.replace(x.hints, crop_path=crop) if x.hints else None
        event = {"step": self.step, "ts": time.time(), "tool": tool, "args": args, "result": result,
                 "shot": self._save("shots", x.shot_png), "crop": crop,
                 "hints": asdict(hints) if hints else None, "human_entry": x.human_entry,
                 "extra": x.extra}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
        return self.step


RUN_JSON_VERSION = 1


def write_run_json(run_dir: pathlib.Path, cfg: DiscoveryConfig, start_url: str, run_id: str,
                   sitemap_pages: int) -> pathlib.Path:
    """M3: runs/<run_id>/run.json, written once at run start. Replay reads it for the Q10 check
    (same viewport / scale / zoom, or refuse to run). Format (version 1):
        {"version": 1, "run_id": str, "start_url": str,
         "viewport": {"width": int, "height": int}, "device_scale_factor": int,
         "zoom": 1.0, "sitemap_pages": int, "created": float (unix time)}
    Only allowed-host start URLs are written; nothing else about the page or the user."""
    if not host_allowed(start_url):
        raise PermissionError(f"start_url is not on the allowed site: {start_url}")
    data = {"version": RUN_JSON_VERSION, "run_id": run_id, "start_url": start_url,
            "viewport": {"width": cfg.viewport[0], "height": cfg.viewport[1]},
            "device_scale_factor": cfg.scale, "zoom": 1.0, "sitemap_pages": sitemap_pages,
            "created": time.time()}
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "run.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return path


def assert_no_secret(run_dir: pathlib.Path, value: str) -> None:
    """Fail if `value` appears (as bytes) in any file under run_dir."""
    needle = value.encode()
    for f in run_dir.rglob("*"):
        if f.is_file() and needle in f.read_bytes():
            raise AssertionError(f"secret value found in {f.relative_to(run_dir)}")


def _test_event_log(run: pathlib.Path) -> None:
    log = EventLog(run)
    assert (run / "shots").is_dir()
    assert (run / "crops").is_dir()
    assert log.path == run / "events.jsonl"
    assert log.record("observe", {}, "OK", EventExtras(shot_png=b"\x89PNG-shot")) == 1
    hints = RungHints("Password", None, None, None)
    assert log.record("type_secret", {"secret_name": "password"}, "OK",
                      EventExtras(crop_png=b"\x89PNG-crop", hints=hints)) == 2
    assert log.record("click", {"ref": 7}, "OK", EventExtras(human_entry=True, extra={"v": "ask"})) == 3
    lines = [json.loads(line) for line in log.path.read_text().splitlines()]
    assert [e["step"] for e in lines] == [1, 2, 3]
    assert lines[0]["shot"] == "shots/001.png"
    assert lines[0]["crop"] is None
    assert lines[1]["crop"] == "crops/002.png"
    assert lines[1]["hints"]["crop_path"] == "crops/002.png", "M2: hints.crop_path = the saved crop"
    assert (run / lines[1]["hints"]["crop_path"]).read_bytes() == b"\x89PNG-crop"
    assert lines[2]["hints"] is None
    assert lines[2]["human_entry"] is True
    assert set(lines[0]) == {"step", "ts", "tool", "args", "result", "shot", "crop", "hints",
                             "human_entry", "extra"}
    try:
        log.record("type_secret", {"value_secret": "x"}, "OK")
        raise AssertionError("value_secret must be refused")
    except ValueError:
        pass
    assert len(log.path.read_text().splitlines()) == 3


def _test_run_json(run: pathlib.Path) -> None:
    path = write_run_json(run, CFG, BASE + "/index.htm", "r1", 0)
    data = json.loads(path.read_text())
    assert path == run / "run.json"
    assert data["viewport"] == {"width": 1280, "height": 800}
    assert data["device_scale_factor"] == 1
    assert data["zoom"] == 1.0
    assert data["run_id"] == "r1"
    assert data["sitemap_pages"] == 0
    assert data["version"] == RUN_JSON_VERSION
    try:
        write_run_json(run, CFG, "https://evil.com/", "r2", 0)
        raise AssertionError("an off-host start_url must be refused")
    except PermissionError:
        pass


def _test_no_secret(run: pathlib.Path) -> None:
    assert_no_secret(run, "hunter2-fake-secret")
    (run / "leak.txt").write_text("oops hunter2-fake-secret")
    caught = ""
    try:
        assert_no_secret(run, "hunter2-fake-secret")
    except AssertionError as exc:
        caught = str(exc)
    assert "leak.txt" in caught, "assert_no_secret must catch a leak"


with tempfile.TemporaryDirectory() as _tmp:
    _run = pathlib.Path(_tmp) / "run1"
    _test_event_log(_run)
    _test_run_json(_run)
    _test_no_secret(_run)
print("OK OFFLINE 14")


# %% OFFLINE 4a: site lock over CDP (Q-A)
import contextlib


class CdpSiteLock:
    """SiteLock over the site tab's own CDP session. `during()` lifts the lock only for our own action."""

    def __init__(self, cdp) -> None:
        self._cdp = cdp
        self.locked = False

    async def _set(self, ignore: bool) -> None:
        await self._cdp.send("Input.setIgnoreInputEvents", {"ignore": ignore})
        self.locked = ignore

    async def lock(self) -> None:
        await self._set(True)

    async def unlock(self) -> None:
        await self._set(False)

    @contextlib.asynccontextmanager
    async def during(self):
        await self.unlock()
        try:
            yield
        finally:
            await self.lock()


class FakeCdp:
    """TEST ONLY. Records every CDP call."""
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send(self, method: str, params: dict | None = None) -> dict:
        self.calls.append((method, params or {}))
        return {}


async def _test_lock() -> None:
    cdp = FakeCdp()
    lk = CdpSiteLock(cdp)
    await lk.lock()
    assert lk.locked and cdp.calls == [("Input.setIgnoreInputEvents", {"ignore": True})]
    async with lk.during():
        assert not lk.locked
    assert [p["ignore"] for _, p in cdp.calls] == [True, False, True] and lk.locked
    try:
        async with lk.during():
            raise ValueError("boom")
    except ValueError:
        pass
    assert lk.locked and cdp.calls[-1] == ("Input.setIgnoreInputEvents", {"ignore": True})


run_sync(_test_lock())
print("OK OFFLINE 4a")


# %% OFFLINE 4b: control window (Q-A: the ONLY place a human acts; no take over)
import base64
import itertools

_CONTROL_CSS = """
body { font: 15px system-ui, sans-serif; margin: 0; padding: 16px; background: #f6f6f4; color: #1d1d1b; }
#status { font-size: 13px; color: #555; margin-bottom: 12px; }
h1 { font-size: 18px; margin: 0 0 8px; }
#details { white-space: pre-wrap; margin-bottom: 12px; }
img { max-width: 100%; border: 1px solid #999; margin: 6px 0; display: block; }
input, textarea { width: 100%; box-sizing: border-box; font: inherit; padding: 6px; margin: 4px 0 10px; }
textarea { height: 120px; }
button { font: inherit; padding: 8px 18px; margin-right: 8px; cursor: pointer; }
#approveBtn { background: #1f6f3f; color: #fff; border: 0; }
#rejectBtn { background: #9b1c1c; color: #fff; border: 0; }
.pane { display: none; }
"""

_CONTROL_JS = """
let current = null;
const $ = id => document.getElementById(id);
function send(extra) {
  if (current === null) return;
  const msg = Object.assign({id: current}, extra);
  current = null;
  for (const p of document.querySelectorAll('.pane')) p.style.display = 'none';
  $('title').textContent = 'Sent. Waiting for the next step...';
  $('details').textContent = '';
  $('image').style.display = 'none';
  window.cuaReply(JSON.stringify(msg));
}
function showImage(el, src) {
  if (src && src.startsWith('data:image/png;base64,')) { el.src = src; el.style.display = 'block'; }
  else { el.removeAttribute('src'); el.style.display = 'none'; }
}
function buildFields(labels, images) {
  const box = $('fields');
  box.replaceChildren();
  labels.forEach((label, i) => {
    const cap = document.createElement('label');
    cap.textContent = label;
    const img = document.createElement('img');
    showImage(img, images[i]);
    const inp = document.createElement('input');
    inp.type = 'text'; inp.autocomplete = 'off'; inp.className = 'multi';
    box.append(cap, img, inp);
  });
}
window.cuaShow = function (p) {
  if (p.mode === 'status') { $('status').textContent = p.status; return; }
  current = p.id;
  for (const pane of document.querySelectorAll('.pane')) pane.style.display = 'none';
  $('title').textContent = p.title || '';
  $('details').textContent = p.details || '';
  showImage($('image'), p.image);
  if (p.mode === 'value') {
    $('value').value = ''; $('value').type = p.masked ? 'password' : 'text';
  }
  if (p.mode === 'values') buildFields(p.labels || [], p.images || []);
  if (p.mode === 'text') $('text').value = '';
  $(p.mode + 'Pane').style.display = 'block';
};
$('approveBtn').onclick = () => send({decision: 'approve'});
$('rejectBtn').onclick = () => send({decision: 'reject'});
$('valueBtn').onclick = () => send({value: $('value').value});
$('valuesBtn').onclick = () => send({values: [...document.querySelectorAll('input.multi')].map(i => i.value)});
$('textBtn').onclick = () => send({text: $('text').value});
"""

_CONTROL_BODY = """
<div id="status">Starting...</div>
<h1 id="title">Waiting for the agent...</h1>
<div id="details"></div>
<img id="image" alt="target" style="display:none">
<div id="approvePane" class="pane">
  <button id="approveBtn">Approve</button><button id="rejectBtn">Reject</button>
</div>
<div id="valuePane" class="pane">
  <input id="value" type="password" autocomplete="off"><button id="valueBtn">Submit</button>
</div>
<div id="valuesPane" class="pane"><div id="fields"></div><button id="valuesBtn">Submit</button></div>
<div id="textPane" class="pane"><textarea id="text"></textarea><button id="textBtn">Submit</button></div>
"""


def control_html() -> str:
    """Our own self-contained control page (no host, no external URL). Site text is only ever set
    with textContent, never parsed as markup."""
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>Agent control</title>"
            f"<style>{_CONTROL_CSS}</style></head><body>{_CONTROL_BODY}"
            f"<script>{_CONTROL_JS}</script></body></html>")


def png_data_url(png: bytes | None) -> str | None:
    return None if png is None else "data:image/png;base64," + base64.b64encode(png).decode("ascii")


class BrowserControlWindow:
    """ControlWindow over OUR OWN control page. Every ask has a unique id; only the reply carrying
    that id resolves it. Anything that is not exactly "approve" counts as reject (fail closed)."""

    def __init__(self, page) -> None:
        self._page = page
        self._ids = itertools.count(1)
        self._pending: dict[str, asyncio.Future] = {}
        self._closed = False

    async def setup(self) -> None:
        await self._page.expose_function("cuaReply", self._on_reply)
        self._page.on("close", self._on_close)
        await self._page.set_content(control_html())

    def _on_reply(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return
        fut = self._pending.get(msg.get("id")) if isinstance(msg, dict) else None
        if fut is not None and not fut.done():
            fut.set_result(msg)

    def _on_close(self, _page) -> None:
        self._closed = True
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(RuntimeError("control window closed"))

    async def _ask(self, payload: dict) -> dict:
        if self._closed:
            raise RuntimeError("control window closed")
        ask_id = f"ask-{next(self._ids)}"
        fut = asyncio.get_running_loop().create_future()
        self._pending[ask_id] = fut
        try:
            await self._page.evaluate("p => window.cuaShow(p)", {**payload, "id": ask_id})
            return await fut
        finally:
            self._pending.pop(ask_id, None)

    async def approve(self, title: str, details: str, crop_png: bytes | None) -> Decision:
        reply = await self._ask({"mode": "approve", "title": title, "details": details,
                                 "image": png_data_url(crop_png)})
        return "approve" if reply.get("decision") == "approve" else "reject"

    async def ask_value(self, label: str, crop_png: bytes | None, masked: bool) -> str | None:
        reply = await self._ask({"mode": "value", "title": label, "details": "Type the value. "
                                 "The agent will enter it.", "image": png_data_url(crop_png),
                                 "masked": masked})
        value = reply.get("value")
        return value if isinstance(value, str) and value.strip() else None

    async def ask_values(self, labels: list[str], crops: list[bytes | None]) -> list[str | None]:
        if len(labels) != len(crops):
            raise ValueError("one crop (or None) per label")
        reply = await self._ask({"mode": "values", "title": "Fill in these fields",
                                 "details": "", "image": None, "labels": list(labels),
                                 "images": [png_data_url(c) for c in crops]})
        values = reply.get("values")
        if not isinstance(values, list) or len(values) != len(labels):
            raise RuntimeError("control window returned the wrong number of values")
        return [v if isinstance(v, str) and v.strip() else None for v in values]

    async def ask_text(self, question: str) -> str:
        reply = await self._ask({"mode": "text", "title": question, "details": "", "image": None})
        text = reply.get("text")
        return text if isinstance(text, str) else ""

    async def status(self, text: str) -> None:
        if not self._closed:
            await self._page.evaluate("p => window.cuaShow(p)", {"mode": "status", "status": text})


class FakeControlPage:
    """TEST ONLY. Stands in for our own control page; `answer(payload)` plays the human."""
    def __init__(self, answer) -> None:
        self.answer = answer
        self.html = ""
        self.payloads: list[dict] = []
        self.bound: dict = {}
        self.handlers: dict = {}

    async def expose_function(self, name: str, callback) -> None:
        self.bound[name] = callback

    async def set_content(self, html: str) -> None:
        self.html = html

    def on(self, event: str, handler) -> None:
        self.handlers[event] = handler

    async def evaluate(self, expression: str, payload: dict) -> None:
        assert expression == "p => window.cuaShow(p)"
        self.payloads.append(payload)
        reply = self.answer(payload)
        if reply is not None:
            self.bound["cuaReply"](json.dumps({"id": payload.get("id"), **reply}))


_html = control_html()
assert "http" not in _html.casefold(), "control page must be self-contained"
assert "take over" not in _html.casefold() and "takeover" not in _html.casefold()
assert "cuaReply" in _html and "cuaShow" in _html and "password" in _html
assert "innerHTML" not in _html, "OCR/site text must be shown as text, never as markup"


def _human(payload: dict) -> dict | None:
    """TEST ONLY scripted human."""
    mode = payload["mode"]
    if mode == "status":
        return None
    if mode == "approve":
        return {"decision": "approve" if "ok" in payload["title"] else "reject"}
    if mode == "value":
        return {"value": "" if "empty" in payload["title"] else "42 Main St"}
    if mode == "values":
        return {"values": ["a", ""]}
    return {"text": "the answer"}


async def _test_control() -> None:
    page = FakeControlPage(_human)
    win = BrowserControlWindow(page)
    await win.setup()
    assert page.html == _html and "cuaReply" in page.bound
    assert await win.approve("ok to pay?", "Pay $10", b"\x89PNG") == "approve"
    assert page.payloads[-1]["image"].startswith("data:image/png;base64,")
    assert await win.approve("pay?", "Pay $10", None) == "reject"
    assert page.payloads[-1]["image"] is None
    assert await win.ask_value("Address", None, masked=False) == "42 Main St"
    assert await win.ask_value("empty SSN", None, masked=True) is None
    assert page.payloads[-1]["masked"] is True
    assert await win.ask_values(["City", "Zip"], [None, b"x"]) == ["a", None]
    assert await win.ask_text("Which account?") == "the answer"
    await win.status("working")
    assert page.payloads[-1] == {"mode": "status", "status": "working"}
    ids = [p["id"] for p in page.payloads if "id" in p]
    assert len(ids) == len(set(ids)), "every ask has its own id"


async def _test_control_safety() -> None:
    # A reply with a stale id or an unknown decision must never count as Approve.
    page = FakeControlPage(lambda p: None)
    win = BrowserControlWindow(page)
    await win.setup()
    task = asyncio.create_task(win.approve("pay?", "x", None))
    await asyncio.sleep(0)
    page.bound["cuaReply"](json.dumps({"id": "stale", "decision": "approve"}))
    await asyncio.sleep(0)
    assert not task.done()
    page.bound["cuaReply"](json.dumps({"id": page.payloads[-1]["id"], "decision": "APPROVE!"}))
    assert await task == "reject"
    task = asyncio.create_task(win.approve("pay?", "x", None))
    await asyncio.sleep(0)
    page.handlers["close"](page)  # control window closed mid-ask: fail closed, never hang
    try:
        await task
        raise AssertionError("closing the control window must fail the ask")
    except RuntimeError:
        pass


run_sync(_test_control())
run_sync(_test_control_safety())
print("OK OFFLINE 4b")


# %% OFFLINE 4c: PlaywrightSurface (pure visual: pixels in, mouse/keyboard out)
import inspect


class PlaywrightSurface:
    """Surface over the SITE page. Pixels in (screenshot), mouse/keyboard out, goto on allowed hosts.
    Every input call lifts the site lock only for itself (lock.during())."""

    def __init__(self, page, lock: SiteLock) -> None:
        self._page = page
        self._lock = lock

    @property
    def url(self) -> str:
        return self._page.url

    async def screenshot(self) -> bytes:
        return await self._page.screenshot(type="png")

    async def click(self, x: int, y: int) -> None:
        async with self._lock.during():
            await self._page.mouse.click(x, y)

    async def type(self, text: str) -> None:
        async with self._lock.during():
            await self._page.keyboard.type(text)

    async def press(self, key: str) -> None:
        async with self._lock.during():
            await self._page.keyboard.press(key)

    async def wheel(self, dx: int, dy: int, x: int | None = None, y: int | None = None) -> None:
        async with self._lock.during():
            if x is not None and y is not None:
                await self._page.mouse.move(x, y)
            await self._page.mouse.wheel(dx, dy)

    async def goto(self, url: str) -> None:
        if not host_allowed(url):
            raise PermissionError(f"host not allowed: {url}")
        try:
            await self._page.goto(url)
        finally:
            await self._lock.lock()  # belt and braces: a navigation must never leave the site open


class FakeSiteLock:
    """TEST ONLY. `open` is True only inside during()."""
    def __init__(self) -> None:
        self.open = False
        self.windows = 0

    async def lock(self) -> None:
        self.open = False

    async def unlock(self) -> None:
        self.open = True

    @contextlib.asynccontextmanager
    async def during(self):
        self.open, self.windows = True, self.windows + 1
        try:
            yield
        finally:
            self.open = False


class _FakeInput:
    def __init__(self, log: list, lock: FakeSiteLock, kind: str) -> None:
        self._log, self._lock, self._kind = log, lock, kind

    def __getattr__(self, name: str):
        async def call(*args):
            self._log.append((f"{self._kind}.{name}", args, self._lock.open))
        return call


class FakePage:
    """TEST ONLY. Records mouse/keyboard/goto calls plus whether the lock was open at that moment."""
    def __init__(self, lock: FakeSiteLock) -> None:
        self.log: list[tuple[str, tuple, bool]] = []
        self.url = "https://parabank.parasoft.com/parabank/index.htm"
        self.mouse = _FakeInput(self.log, lock, "mouse")
        self.keyboard = _FakeInput(self.log, lock, "keyboard")

    async def screenshot(self, type: str) -> bytes:
        assert type == "png"
        return b"PNG"

    async def goto(self, url: str) -> None:
        self.log.append(("goto", (url,), False))


async def _test_surface() -> None:
    lock = FakeSiteLock()
    page = FakePage(lock)
    s = PlaywrightSurface(page, lock)
    assert s.url == page.url and await s.screenshot() == b"PNG"
    await s.click(10, 20)
    await s.type("hello")
    await s.press("Enter")
    await s.wheel(0, 600)
    await s.wheel(0, -600, x=640, y=400)
    assert [(n, a) for n, a, _ in page.log] == [
        ("mouse.click", (10, 20)), ("keyboard.type", ("hello",)), ("keyboard.press", ("Enter",)),
        ("mouse.wheel", (0, 600)), ("mouse.move", (640, 400)), ("mouse.wheel", (0, -600))]
    assert all(opened for _, _, opened in page.log), "every input call runs inside lock.during()"
    assert lock.windows == 5 and not lock.open
    await s.goto("https://parabank.parasoft.com/parabank/overview.htm")
    for bad in ("https://evil.com/", "http://localhost/", "file:///etc/passwd"):
        try:
            await s.goto(bad)
            raise AssertionError(bad)
        except PermissionError:
            pass
    assert [a for n, a, _ in page.log if n == "goto"] == [("https://parabank.parasoft.com/parabank/overview.htm",)]
    lock.open = True  # pretend a navigation dropped the lock: goto must always re-lock
    await s.goto("https://parabank.parasoft.com/parabank/index.htm")
    assert not lock.open


FORBIDDEN_ON_SITE = ("evaluate", "locator", "fill", "select_option", "get_by_", "query_selector",
                     "inner_text", "content", "accessibility", "add_init_script", "expose_function",
                     "expose_binding", "set_content")


def _surface_names(cls: type) -> set[str]:
    """Every attribute/global name the class's methods touch (from bytecode, so docstrings don't count)."""
    names: set[str] = set()
    for member in vars(cls).values():
        fn = member.fget if isinstance(member, property) else member
        code = getattr(fn, "__code__", None)
        if code is not None:
            names |= set(code.co_names)
    return names


run_sync(_test_surface())
_names = _surface_names(PlaywrightSurface)
assert not [f for f in FORBIDDEN_ON_SITE if any(f in n for n in _names)], _names
try:  # also scan the text when the source is available (Jupyter); the runner's exec has no source file
    _src = inspect.getsource(PlaywrightSurface)
    assert not [f for f in FORBIDDEN_ON_SITE if f in _src]
except (OSError, TypeError):
    pass
print("OK OFFLINE 4c")


# %% [markdown]
# ## The pure-visual discovery agent (OFFLINE 16-19)
# One run's state lives in `AgentState`; every tool is a free `async def tool(st, ...) -> str`
# (composition, see `parts/AGENT_CONTRACT.md`). The agent only drives the `Surface` (pixels in,
# mouse/keyboard out). No DOM reads anywhere; it only ever sees a screenshot + OCR text.


# %% OFFLINE 16: AgentState + core tools (observe, click, click_at) + FakeSurface / FakeControl
from collections.abc import Mapping
from urllib.parse import urlparse

Screen = tuple[bytes, list[tuple[str, Box, float]]]


@dataclass
class AgentState:
    """One discovery run. Tools are free functions over this (composition, AGENT_CONTRACT.md)."""
    surface: Surface
    ocr: OcrEngine
    cfg: DiscoveryConfig
    log: EventLog
    lock: SiteLock
    control: ControlWindow
    given_text: str                  # the goal text; values not in it need a human (type_text rule)
    secrets: Mapping[str, str]       # NAME -> value, already filtered to the current origin
    counter: RefCounter = field(default_factory=RefCounter)
    look: Look | None = None         # latest screen; None before the first observe
    declined: set[str] = field(default_factory=set)       # normalised texts a human rejected
    login_failures: int = 0
    saved: dict[str, str] = field(default_factory=dict)   # extract_value results
    act_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def page(self) -> str:
        """Last path segment of the current URL, e.g. "index.htm" ("" for a bare folder)."""
        return urlparse(self.surface.url).path.rsplit("/", 1)[-1]


async def fresh_look(st: AgentState) -> Look:
    """Screenshot -> OCR -> run-wide numbering -> st.look (gen goes up by one)."""
    png = await st.surface.screenshot()
    elements = number(st.ocr(png), st.counter)
    st.look = Look((st.look.gen + 1) if st.look else 1, png, elements)
    return st.look


async def act(st: AgentState, fn: Callable[[], Awaitable[None]]) -> None:
    """The ONLY way to touch the site: one action at a time, lock lifted just for it (Q-A)."""
    async with st.act_lock:
        async with st.lock.during():
            await fn()


def before_crop(st: AgentState, target: Element | Point) -> bytes:
    """Rung-3 picture, cut from the look BEFORE the action (Q7b/Q14); neighbours blanked."""
    assert st.look is not None, "before_crop needs a look"
    keep = target.ref if isinstance(target, Element) else None
    return cut_crop(st.look.png, crop_box_for(target, st.cfg), st.look.elements, keep)


def hints_for(st: AgentState, target: Element | Point) -> RungHints:
    """Replay hints for the target on the current (pre-action) look. crop_path is filled by the log."""
    assert st.look is not None, "hints_for needs a look"
    els = st.look.elements
    if isinstance(target, Element):
        return RungHints(target.text, nearest_anchor(els, target.box.center, st.cfg), None,
                         infer_table_cell(els, target.ref))
    return RungHints(None, nearest_anchor(els, target, st.cfg), None, None)


def _dup_count(st: AgentState, norm: str) -> int:
    els = st.look.elements if st.look else ()
    return sum(1 for e in els if normalise(e.text) == norm)


async def gate_click(st: AgentState, text: str | None, crop: bytes) -> str | None:
    """Q-B: deny words refused; safe-list clicks go ahead; everything else asks the human.
    A rejected text is remembered: asking again returns DECLINED with no second prompt.
    Text-less (click_at) rejections are not remembered: there is no text to key them on."""
    norm = normalise(text)
    verdict = classify_click(text, st.cfg, st.page(), _dup_count(st, norm))
    label = repr(text) if norm else "a spot with no text"
    if verdict == "deny":
        return f"REFUSED: clicking {label} is not allowed (deny list). Choose another way."
    if norm and norm in st.declined:
        return f"DECLINED: the human already rejected clicking {label}. Do not try it again."
    if verdict == "safe":
        return None
    details = f"Page {st.page()}: the agent wants to click {label}."
    if await st.control.approve(f"Click {label}?", details, crop) == "approve":
        return None
    if norm:
        st.declined.add(norm)
    return f"DECLINED: the human rejected clicking {label}. Do not try it again."


def _login_check(st: AgentState, look: Look) -> str | None:
    """D69: count screens showing a login-failure text; STOP at the configured limit."""
    shown = look.text().casefold()
    if not any(t.casefold() in shown for t in st.cfg.login_failure_texts):
        return None
    st.login_failures += 1
    limit = st.cfg.login_attempt_limit
    if st.login_failures >= limit:
        return f"STOP: login failed {st.login_failures} times (limit {limit}). Ask a human."
    return f"Login failed ({st.login_failures}/{limit})."


def _stopped(st: AgentState) -> str | None:
    if st.login_failures >= st.cfg.login_attempt_limit:
        return f"STOP: login failed {st.login_failures} times. No more actions."
    return None


def _record(st: AgentState, tool: str, args: dict[str, object], result: str,
            extras: EventExtras | None = None) -> str:
    st.log.record(tool, args, result, extras)
    return result


async def _perform(st: AgentState, call: tuple[str, dict[str, object]],
                   fn: Callable[[], Awaitable[None]], crop: bytes | None,
                   hints: RungHints | None) -> str:
    """act -> fresh_look -> result text -> one log line (shot + crop from BEFORE the action)."""
    tool, args = call
    before = st.look
    await act(st, fn)
    after = await fresh_look(st)
    stop = _login_check(st, after)
    if stop and stop.startswith("STOP"):
        result = stop
    elif before is not None and screens_same(before.png, after.png, st.cfg):
        result = "NO CHANGE: the screen looks the same after that action. Try something else."
    else:
        head = f"OK: {tool} done. {stop or ''}".rstrip()
        result = f"{head}\nNew screen (gen {after.gen}, page {st.page()}):\n{format_elements(after.elements)}"
    shot = before.png if before else None
    return _record(st, tool, args, result, EventExtras(shot_png=shot, crop_png=crop, hints=hints))


async def observe(st: AgentState) -> str:
    look = await fresh_look(st)
    text = f"Screen gen {look.gen} (page {st.page()}):\n{format_elements(look.elements)}"
    return _record(st, "observe", {}, text, EventExtras(shot_png=look.png))


async def click(st: AgentState, ref: int) -> str:
    """Click the centre of box [ref] on the latest screen. The exact ref, never a text lookup."""
    args: dict[str, object] = {"ref": ref}
    if st.look is None:
        return _record(st, "click", args, "REFUSED: call observe first")
    blocked = _stopped(st)
    target = blocked or resolve_target(st.look, ref, None, None, st.cfg)
    if isinstance(target, str):
        return _record(st, "click", args, target)
    el = st.look.by_ref(ref)
    crop, hints = before_crop(st, el), hints_for(st, el)
    gate = await gate_click(st, el.text, crop)
    if gate:
        return _record(st, "click", args, gate, EventExtras(crop_png=crop, hints=hints))
    return await _perform(st, ("click", args), lambda: st.surface.click(target.x, target.y), crop, hints)


async def click_at(st: AgentState, x: int, y: int) -> str:
    """Click a text-less point (an empty input box, an icon). Always asks a human (Q-B)."""
    args: dict[str, object] = {"x": x, "y": y}
    if st.look is None:
        return _record(st, "click_at", args, "REFUSED: call observe first")
    target = _stopped(st) or resolve_target(st.look, None, x, y, st.cfg)
    if isinstance(target, str):
        return _record(st, "click_at", args, target)
    crop, hints = before_crop(st, target), hints_for(st, target)
    gate = await gate_click(st, None, crop)
    if gate:
        return _record(st, "click_at", args, gate, EventExtras(crop_png=crop, hints=hints))
    return await _perform(st, ("click_at", args), lambda: st.surface.click(target.x, target.y), crop, hints)


class FakeSurface:
    """TEST ONLY. Scripted screens [(png, ocr_items)]; every action advances one screen (clamped
    at the last) unless `stay` is True (persistent until reset). Records every call."""

    def __init__(self, screens: list[Screen], url: str) -> None:
        self.screens, self.url = screens, url
        self.calls: list[tuple] = []
        self.stay = False
        self._i = 0

    def _advance(self, call: tuple) -> None:
        self.calls.append(call)
        if not self.stay:
            self._i = min(self._i + 1, len(self.screens) - 1)

    def ocr(self, png: bytes) -> list[tuple[str, Box, float]]:
        match = next((found for p, found in self.screens if p == png), None)
        return list(match if match is not None else self.screens[self._i][1])

    async def screenshot(self) -> bytes:
        return self.screens[self._i][0]

    async def click(self, x: int, y: int) -> None:
        self._advance(("click", x, y))

    async def type(self, text: str) -> None:
        self._advance(("type", text))

    async def press(self, key: str) -> None:
        self._advance(("press", key))

    async def wheel(self, dx: int, dy: int, x: int | None = None, y: int | None = None) -> None:
        self._advance(("wheel", dx, dy))

    async def goto(self, url: str) -> None:
        self.url = url
        self._advance(("goto", url))


class FakeControl:
    """TEST ONLY. Scripted human answers (fail closed when a queue runs out: reject / None / "")."""

    def __init__(self, decisions: list[str] = (), values: list[str | None] = (),
                 texts: list[str] = ()) -> None:
        self.decisions, self.values, self.texts = list(decisions), list(values), list(texts)
        self.prompts: list[tuple[str, str]] = []
        self.crops: list[bytes | None] = []
        self.statuses: list[str] = []

    async def approve(self, title: str, details: str, crop_png: bytes | None) -> Decision:
        self.prompts.append(("approve", title))
        self.crops.append(crop_png)
        return "approve" if self.decisions and self.decisions.pop(0) == "approve" else "reject"

    async def ask_value(self, label: str, crop_png: bytes | None, masked: bool) -> str | None:
        self.prompts.append(("value", label))
        self.crops.append(crop_png)
        return self.values.pop(0) if self.values else None

    async def ask_values(self, labels: list[str], crops: list[bytes | None]) -> list[str | None]:
        self.prompts.append(("values", ", ".join(labels)))
        return [self.values.pop(0) if self.values else None for _ in labels]

    async def ask_text(self, question: str) -> str:
        self.prompts.append(("text", question))
        return self.texts.pop(0) if self.texts else ""

    async def status(self, text: str) -> None:
        self.statuses.append(text)


print("OK OFFLINE 16")


# %% OFFLINE 16t: tests for the agent core
_URL16 = "https://parabank.parasoft.com/parabank/index.htm"
_S1 = (render_screen([("Username", 100, 211), ("Log In", 210, 291)]),
       items(("Username", 100, 200, 190, 222), ("Log In", 210, 280, 270, 302)))


def _banner(labels: list[tuple[str, int, int]]) -> bytes:
    """A screen with a big dark banner, so it clearly differs from the others (MAD >> 1)."""
    img = png_to_bgr(render_screen(labels))
    img[400:700, :] = 40
    return bgr_to_png(img)


_S2 = (_banner([("Welcome", 100, 211)]), items(("Welcome", 100, 200, 190, 222)))
_S3 = (render_screen([("Register", 100, 211)]), items(("Register", 100, 200, 190, 222)))


class _LockProbeSurface(FakeSurface):
    """TEST ONLY: records whether the site lock was open at each mouse/keyboard call."""
    probe: FakeSiteLock | None = None
    opens: list[bool] = []

    async def click(self, x: int, y: int) -> None:
        self.opens.append(bool(self.probe and self.probe.open))
        await super().click(x, y)


def _state16(screens: list, decisions: list[str] = (), cfg: DiscoveryConfig = CFG) -> AgentState:
    fs = _LockProbeSurface(list(screens), _URL16)
    lock = FakeSiteLock()
    fs.probe, fs.opens = lock, []
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3_agent_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=cfg, log=EventLog(run), lock=lock,
                      control=FakeControl(decisions=list(decisions)), given_text="read a balance",
                      secrets={})


def _events(st: AgentState) -> list[dict]:
    return [json.loads(line) for line in st.log.path.read_text().splitlines()]


async def _test_16_click() -> None:
    _safe = dataclasses.replace(CFG, safe_clicks=frozenset({("index.htm", "Log In")}))
    st = _state16([_S1, _S2], cfg=_safe)
    assert st.page() == "index.htm"
    seen = await observe(st)
    assert "'Log In'" in seen and "[2]" in seen, seen
    before_png = st.look.png
    out = await click(st, 2)
    assert st.surface.calls == [("click", 240, 291)], st.surface.calls
    assert not out.startswith(("REFUSED", "STALE", "DECLINED")), out
    assert st.control.prompts == [], "a safe-list click asks no one"
    assert st.surface.opens == [True], "the lock is open during our own act()"
    assert st.lock.open is False and st.lock.windows == 1, "locked again afterwards"
    ev = _events(st)
    assert [e["tool"] for e in ev] == ["observe", "click"], "one log line per call"
    crop = (st.log.run_dir / ev[1]["crop"]).read_bytes()
    el = Look(1, before_png, number(_S1[1], RefCounter())).by_ref(2)
    assert crop == cut_crop(before_png, crop_box_for(el, CFG), (el,), el.ref), "crop from the look BEFORE"
    assert ev[1]["hints"]["text"] == "Log In" and ev[1]["hints"]["crop_path"] == ev[1]["crop"]
    stale = await click(st, 2)
    assert stale.startswith("STALE"), stale
    assert st.surface.calls == [("click", 240, 291)], "a stale ref never touches the mouse"
    assert len(_events(st)) == 3


async def _test_16_gates() -> None:
    st = _state16([_S3, _S2])
    await observe(st)
    denied = await click(st, 1)
    assert denied.startswith("REFUSED") and st.surface.calls == [] and st.control.prompts == []
    st = _state16([_S1, _S2], decisions=["reject"])
    await observe(st)
    first = await click(st, 2)
    assert first.startswith("DECLINED:") and len(st.control.prompts) == 1, (first, st.control.prompts)
    again = await click(st, 2)
    assert again.startswith("DECLINED:") and len(st.control.prompts) == 1, "no second prompt"
    assert st.surface.calls == [] and st.lock.windows == 0
    assert len(_events(st)) == 3


async def _test_16_click_at() -> None:
    st = _state16([_S1, _S2], decisions=["approve", "approve"])
    await observe(st)
    st.surface.stay = True
    same = await click_at(st, 400, 500)
    assert same.startswith("NO CHANGE"), same
    assert st.surface.calls == [("click", 400, 500)] and st.control.prompts[0][0] == "approve"
    st.surface.stay = False
    moved = await click_at(st, 400, 500)
    assert not moved.startswith("NO CHANGE"), moved
    ev = _events(st)[-1]
    assert ev["hints"]["text"] is None and ev["hints"]["anchor"] is None
    assert (await click_at(st, 5000, 5)).startswith("REFUSED")
    assert st.lock.open is False and st.surface.opens == [True, True]


async def _test_16_login_limit() -> None:
    fail = (_banner([("could not be verified", 100, 211)]),
            items(("The username and password could not be verified.", 100, 200, 500, 222)))
    cfg = dataclasses.replace(CFG, login_attempt_limit=2)
    st = _state16([_S1, fail, fail, fail], decisions=["approve"] * 3, cfg=cfg)
    await observe(st)
    await click(st, 2)
    assert st.login_failures == 1
    await observe(st)
    stop = await click_at(st, 300, 300)
    assert st.login_failures == 2 and stop.startswith("STOP:"), stop


run_sync(_test_16_click())
run_sync(_test_16_gates())
run_sync(_test_16_click_at())
run_sync(_test_16_login_limit())
print("OK OFFLINE 16t")

# CONTRACT READY


# %% OFFLINE 17: typing (type_text, type_secret) by a number or a point
SELECT_ALL_KEY = "ControlOrMeta+A"   # replace whatever the box already holds


@dataclass(frozen=True)
class _TypeJob:
    """One typing action, fixed before the keys go out (crop + hints from the look BEFORE)."""
    tool: str
    args: dict[str, object]
    point: Point
    box: Box                  # where the typed text must show up on the re-read
    crop: bytes
    hints: RungHints
    human: bool = False       # a human gave the value: never shown to the model or logged
    secret: bool = False      # a named secret: masking dots only, never shown or logged


def _where(ref: int | None, x: int | None, y: int | None) -> dict[str, object]:
    return {"ref": ref} if ref is not None else {"x": x, "y": y}


def _type_target(st: AgentState, ref: int | None, x: int | None,
                 y: int | None) -> tuple[Point, Element | Point] | str:
    """The click point + the thing to crop/hint (the element for a ref, else the point)."""
    if st.look is None:
        return "REFUSED: call observe first"
    got = _stopped(st) or resolve_target(st.look, ref, x, y, st.cfg)
    if isinstance(got, str):
        return got
    el = st.look.by_ref(ref) if ref is not None else None
    return got, (el or got)


def _field_label(st: AgentState, target: Element | Point) -> str:
    """The field's name for the human: its nearest label, else its own text."""
    centre = target.box.center if isinstance(target, Element) else target
    anchor = nearest_anchor(st.look.elements, centre, st.cfg)
    if anchor:
        return anchor.label
    return target.text if isinstance(target, Element) else f"the box at ({centre.x}, {centre.y})"


def _sensitive(st: AgentState, label: str) -> bool:
    return any(w in label.casefold() for w in st.cfg.sensitive_words)


def _in_goal(st: AgentState, value: str) -> bool:
    v = " ".join(value.casefold().split())
    return bool(v) and v in " ".join(st.given_text.casefold().split())


def _scrub_box(st: AgentState, box: Box) -> None:
    """Drop every OCR element inside the typed box from the latest look (never shown on)."""
    kept = tuple(e for e in st.look.elements if not _contains(box, e.box.center))
    st.look = Look(st.look.gen, st.look.png, kept)


def _read_ok(read: str, value: str, job: _TypeJob) -> bool:
    return typed_ok(read, value, secret=True) or (not job.secret and typed_ok(read, value, False))


async def _key_in(st: AgentState, point: Point, value: str) -> None:
    async def keys() -> None:
        await st.surface.click(point.x, point.y)
        await st.surface.press(SELECT_ALL_KEY)
        await st.surface.type(value)
    await act(st, keys)


async def _reread(st: AgentState, job: _TypeJob, value: str) -> tuple[bool, bool]:
    """Poll fresh looks until the box shows the value (or leaks a secret). -> (ok, leaked)."""
    seen = {"ok": False, "leaked": False}

    async def once() -> bool:
        read = read_box_text((await fresh_look(st)).elements, job.box)
        seen["leaked"] = job.secret and secret_leaked(read, value)
        seen["ok"] = not seen["leaked"] and _read_ok(read, value, job)
        return seen["ok"] or seen["leaked"]
    await poll_until(once, st.cfg.poll_budget_ms, st.cfg.poll_ms)
    return seen["ok"], seen["leaked"]


def _verdict(st: AgentState, job: _TypeJob, ok: bool, leaked: bool) -> str:
    """The text the model gets back. Never the value: for human/secret jobs the box is scrubbed."""
    if leaked:
        _scrub_box(st, job.box)
        return ("STOP: the box shows the secret as plain text (not a masked field). Nothing was "
                "logged. A human must check this field. Do not type it again.")
    if not ok and job.secret:
        return "STOP: the box shows no masking dots after typing the secret. A human must check it."
    if not ok:
        return "NO CHANGE: typed, but the box does not show the text. Call observe and check the field."
    if job.human or job.secret:
        _scrub_box(st, job.box)
    head = "OK: a human entered the value (not shown to you)." if job.human else f"OK: {job.tool} done."
    return f"{head}\nNew screen (gen {st.look.gen}, page {st.page()}):\n{format_elements(st.look.elements)}"


async def _run_job(st: AgentState, job: _TypeJob, value: str) -> str:
    """act (click + select all + type) -> re-read -> verdict -> one log line. The value stays local."""
    shot = st.look.png
    await _key_in(st, job.point, value)
    ok, leaked = await _reread(st, job, value)
    result = _verdict(st, job, ok, leaked)
    if result.startswith("STOP"):
        await st.control.status(f"{job.tool} on page {st.page()} stopped: {result.split(': ', 1)[1]}")
    extras = EventExtras(shot_png=shot, crop_png=job.crop, hints=job.hints, human_entry=job.human)
    return _record(st, job.tool, job.args, result, extras)


async def type_text(st: AgentState, value: str, ref: int | None = None, x: int | None = None,
                    y: int | None = None) -> str:
    """Type `value` into box [ref] or at (x, y). A value not in the goal, or a sensitive field,
    goes to a human in the control window; our code types their answer (never logged)."""
    got = _type_target(st, ref, x, y)
    if isinstance(got, str):
        return _record(st, "type_text", _where(ref, x, y), got)
    point, target = got
    label = _field_label(st, target)
    crop, hints = before_crop(st, target), hints_for(st, target)
    job = _TypeJob("type_text", {"value": value, **_where(ref, x, y)}, point,
                   crop_box_for(target, st.cfg), crop, hints)
    if _in_goal(st, value) and not _sensitive(st, label):
        return await _run_job(st, job, value)
    job = dataclasses.replace(job, args={"field": label, **_where(ref, x, y)}, human=True)
    given = await st.control.ask_value(label, crop, masked=_sensitive(st, label))
    if not given:
        return _record(st, "type_text", job.args, f"DECLINED: no value was given for {label!r}.",
                       EventExtras(crop_png=crop, hints=hints, human_entry=True))
    return await _run_job(st, job, given)


async def type_secret(st: AgentState, name: str, ref: int | None = None, x: int | None = None,
                      y: int | None = None) -> str:
    """Type the secret called `name` (the model never sees the value). Only names allowed for
    this origin (st.secrets), only on an allowed host; the box must then show masking dots."""
    args = {"secret_name": name, **_where(ref, x, y)}
    if name not in st.secrets:
        return _record(st, "type_secret", args,
                       f"REFUSED: unknown secret {name!r}. Known names: {sorted(st.secrets)}")
    if not host_allowed(st.surface.url):
        return _record(st, "type_secret", args, "REFUSED: this site is not on the allowlist.")
    got = _type_target(st, ref, x, y)
    if isinstance(got, str):
        return _record(st, "type_secret", args, got)
    point, target = got
    job = _TypeJob("type_secret", args, point, crop_box_for(target, st.cfg),
                   before_crop(st, target), hints_for(st, target), secret=True)
    return await _run_job(st, job, st.secrets[name])


print("OK OFFLINE 17")


# %% OFFLINE 17t: tests for type_text / type_secret
_URL17 = "https://parabank.parasoft.com/parabank/index.htm"
_BOX17 = Box(250, 195, 450, 225)                      # the empty input box, right of its label
_PT17 = _BOX17.center


def _screen17(label: str, shown: str | None) -> Screen:
    """A label + an input box; `shown` = what the box displays (None = empty)."""
    labels = [(label, 100, 216)] + ([(shown, 260, 216)] if shown else [])
    found = [(label, 100, 200, 200, 222)] + ([(shown, 260, 200, 440, 222)] if shown else [])
    return render_screen(labels, [_BOX17]), items(*found)


def _state17(screens: list[Screen], given: str = "", values: list[str | None] = (),
             secrets: dict[str, str] | None = None) -> AgentState:
    fs = FakeSurface(list(screens), _URL17)
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3c_typing_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=CFG, log=EventLog(run), lock=FakeSiteLock(),
                      control=FakeControl(values=list(values)), given_text=given,
                      secrets=secrets if secrets is not None else {})


def _typed(st: AgentState) -> list[str]:
    return [c[1] for c in st.surface.calls if c[0] == "type"]


async def _test_17_goal_value_by_point() -> None:
    st = _state17([_screen17("Amount", None), _screen17("Amount", "500")], given="pay 500 to rent")
    await observe(st)
    before_png = st.look.png
    out = await type_text(st, "500", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK"), out
    assert st.surface.calls == [("click", _PT17.x, _PT17.y), ("press", SELECT_ALL_KEY),
                                ("type", "500")], st.surface.calls
    assert st.control.prompts == [], "a value from the goal needs no human"
    assert st.lock.windows == 1 and st.lock.open is False
    ev = _events(st)[-1]
    assert ev["tool"] == "type_text" and ev["args"]["value"] == "500" and ev["human_entry"] is False
    assert ev["hints"]["anchor"]["label"] == "Amount"
    crop = (st.log.run_dir / ev["crop"]).read_bytes()
    first = Look(1, before_png, number(_screen17("Amount", None)[1], RefCounter()))
    assert crop == cut_crop(before_png, crop_box_for(_PT17, CFG), first.elements, None), "crop BEFORE"
    assert not any("500" in t for t, _, _ in OCR(crop)), "the box is empty in the crop"


async def _test_17_by_ref() -> None:
    st = _state17([_screen17("Amount", "0.00"), _screen17("Amount", "500")], given="pay 500")
    await observe(st)
    ref = fuzzy_find(st.look.elements, "0.00").ref
    out = await type_text(st, "500", ref=ref)
    assert out.startswith("OK"), out
    assert st.surface.calls[0][0] == "click" and _typed(st) == ["500"]
    assert (await type_text(st, "500", ref=ref)).startswith("STALE"), "an old ref is refused"
    assert (await type_text(st, "500", ref=1, x=5, y=5)).startswith("REFUSED")


async def _test_17_human_value() -> None:
    st = _state17([_screen17("Phone", None), _screen17("Phone", "5550199")], given="pay rent",
                  values=["5550199"])
    await observe(st)
    out = await type_text(st, "1234567", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK") and "human" in out, out
    assert st.control.prompts == [("value", "Phone")], st.control.prompts
    assert _typed(st) == ["5550199"], "our code types the human's value"
    assert "5550199" not in out and "1234567" not in out
    ev = _events(st)[-1]
    assert ev["human_entry"] is True and ev["args"].get("field") == "Phone"
    assert_no_secret(st.log.run_dir, "5550199")
    assert_no_secret(st.log.run_dir, "1234567")


async def _test_17_human_declines() -> None:
    st = _state17([_screen17("Phone", None)], given="pay rent", values=[None])
    await observe(st)
    out = await type_text(st, "1234567", x=_PT17.x, y=_PT17.y)
    assert out.startswith("DECLINED"), out
    assert st.surface.calls == [] and st.lock.windows == 0


async def _test_17_sensitive() -> None:
    st = _state17([_screen17("SSN", None), _screen17("SSN", "•••••")], given="ssn is 123456789",
                  values=["987654321"])
    await observe(st)
    out = await type_text(st, "123456789", x=_PT17.x, y=_PT17.y)
    assert st.control.prompts == [("value", "SSN")], "a sensitive label -> human, even if in goal"
    assert _typed(st) == ["987654321"] and out.startswith("OK"), out
    assert "987654321" not in out
    assert_no_secret(st.log.run_dir, "987654321")


async def _test_17_secret_ok() -> None:
    secret = "hunter2-fake"
    st = _state17([_screen17("Password", None), _screen17("Password", "••••••")],
                  secrets={"password": secret})
    await observe(st)
    out = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK"), out
    assert _typed(st) == [secret], "the fake keyboard gets the value"
    assert secret not in out and st.control.prompts == []
    ev = _events(st)[-1]
    assert ev["args"] == {"secret_name": "password", "x": _PT17.x, "y": _PT17.y}, ev["args"]
    assert_no_secret(st.log.run_dir, secret)


async def _test_17_secret_refused() -> None:
    st = _state17([_screen17("Password", None)], secrets={"password": "hunter2-fake"})
    await observe(st)
    unknown = await type_secret(st, "api_key", x=_PT17.x, y=_PT17.y)
    assert unknown.startswith("REFUSED") and "password" in unknown, unknown
    assert "hunter2-fake" not in unknown
    st.surface.url = "https://evil.example.com/login"
    off = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert off.startswith("REFUSED"), off
    assert st.surface.calls == [] and st.lock.windows == 0


async def _test_17_secret_leak() -> None:
    secret = "hunter2-fake"
    st = _state17([_screen17("Password", None), _screen17("Password", secret)],
                  secrets={"password": secret})
    await observe(st)
    out = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert out.startswith("STOP:"), out
    assert secret not in out
    assert st.control.statuses, "a human is told"
    assert all(secret not in s for s in st.control.statuses)
    assert all(secret not in e.text for e in st.look.elements), "the leaked text is dropped"
    assert_no_secret(st.log.run_dir, secret)


for _t17 in (_test_17_goal_value_by_point, _test_17_by_ref, _test_17_human_value,
             _test_17_human_declines, _test_17_sensitive, _test_17_secret_ok,
             _test_17_secret_refused, _test_17_secret_leak):
    run_sync(_t17())
print("OK OFFLINE 17t")


# %% [markdown]
# ## Navigation tools: scroll, select_option, open_path (OFFLINE 18)
# `scroll` wheels the mouse, then takes a fresh look (new numbers, old ones go stale, Q13).
# `select_option` picks a dropdown option by keyboard through OFFLINE 13's `choose_option` (Q12).
# `open_path` goes straight to a path on the allowed host, behind the deny words and the
# goal-values rule (the cli.py rule). Every action goes through `act()` and writes one log line.


# %% OFFLINE 18: scroll, select_option, open_path (free tools over AgentState)
from urllib.parse import parse_qsl


def _screen_text(st: AgentState, head: str) -> str:
    look = st.look
    return f"{head}\nNew screen (gen {look.gen}, page {st.page()}):\n{format_elements(look.elements)}"


def _scroll_refusal(st: AgentState, direction: str, x: int | None, y: int | None) -> str | None:
    if direction not in ("up", "down"):
        return "REFUSED: direction must be 'up' or 'down'"
    if st.look is None:
        return "REFUSED: call observe first"
    if x is None and y is None:
        return _stopped(st)
    target = _stopped(st) or resolve_target(st.look, None, x, y, st.cfg)
    return target if isinstance(target, str) else None


async def scroll(st: AgentState, direction: Literal["up", "down"], x: int | None = None,
                 y: int | None = None) -> str:
    """Q13: wheel by cfg.scroll_px (over (x, y) when given, for a scrolling panel), then a fresh
    look with NEW numbers; every older number is stale. Same screen before and after = the edge."""
    args: dict[str, object] = {"direction": direction, "x": x, "y": y}
    refused = _scroll_refusal(st, direction, x, y)
    if refused:
        return _record(st, "scroll", args, refused)
    dy = st.cfg.scroll_px if direction == "down" else -st.cfg.scroll_px
    before = st.look
    await act(st, lambda: st.surface.wheel(0, dy, x, y))
    after = await fresh_look(st)
    if screens_same(before.png, after.png, st.cfg):
        edge = "BOTTOM" if direction == "down" else "TOP"
        head = f"{edge} OF PAGE: the screen did not move. Old numbers are stale; use these."
    else:
        head = f"OK: scrolled {direction}. Old numbers are stale; use these."
    return _record(st, "scroll", args, _screen_text(st, head), EventExtras(shot_png=before.png))


def _box_reader(st: AgentState, box: Box) -> Callable[[], Awaitable[str]]:
    """OCR text inside `box` on a new screenshot (no numbering: reading burns no refs)."""
    async def read() -> str:
        found = st.ocr(await st.surface.screenshot())
        return " ".join(t for t, b, _ in found if _contains(box, b.center))
    return read


def _select_target(st: AgentState, option: str, ref: int | None, x: int | None,
                   y: int | None) -> Element | Point | str:
    if st.look is None:
        return "REFUSED: call observe first"
    point = _stopped(st) or resolve_target(st.look, ref, x, y, st.cfg)
    if isinstance(point, str):
        return point
    if normalise(option) not in normalise(st.given_text):
        return (f"ASK_HUMAN: {option!r} is not in the goal. Never guess an option; "
                "use request_value so a human chooses it.")
    return st.look.by_ref(ref) if ref is not None else point


async def select_option(st: AgentState, option: str, ref: int | None = None, x: int | None = None,
                        y: int | None = None) -> str:
    """Q12: pick `option` in the dropdown at [ref] or (x, y) via choose_option (type + Enter,
    ArrowDown fallback up to the config limit), checked by OCR of the dropdown's own box."""
    args: dict[str, object] = {"option": option, "ref": ref, "x": x, "y": y}
    target = _select_target(st, option, ref, x, y)
    if isinstance(target, str):
        return _record(st, "select_option", args, target)
    crop, hints, before = before_crop(st, target), hints_for(st, target), st.look
    point = target.box.center if isinstance(target, Element) else target
    reader = _box_reader(st, crop_box_for(target, st.cfg))
    verdict: list[str] = []

    async def pick() -> None:
        verdict.append(await choose_option(st.surface, point, option, reader, st.cfg))

    await act(st, pick)
    await fresh_look(st)
    head = (f"OK: selected {option!r}." if verdict == ["OK"] else
            f"ASK_HUMAN: could not select {option!r}. Use request_value so a human chooses it.")
    extras = EventExtras(shot_png=before.png, crop_png=crop, hints=hints)
    return _record(st, "select_option", args, _screen_text(st, head), extras)


def path_url(path: str, base: str) -> str | None:
    """A site path -> a full URL on `base`'s origin. A path already under base's folder (a sitemap
    path) is joined to the origin; any other path is joined to base (the cli.py form). Only
    "/..." paths: a scheme, "//host" or a relative path -> None."""
    if not path.startswith("/") or path.startswith("//"):
        return None
    b = urlparse(base)
    folder = b.path.rstrip("/")
    if folder and (path == folder or path.startswith(folder + "/")):
        return f"{b.scheme}://{b.netloc}{path}"
    return f"{b.scheme}://{b.netloc}{folder}{path}"


def open_path_refusal(path: str, given_text: str, cfg: DiscoveryConfig, base: str) -> str | None:
    """The cli.py open_path rules: deny words, every query value from the goal, the host gate."""
    if any(w.casefold() in path.casefold() for w in cfg.deny_words):
        return f"REFUSED: {path!r} is not allowed (deny list)."
    values = [v for _, v in parse_qsl(urlparse(path).query)]
    if any(v.strip().casefold() not in given_text.casefold() for v in values):
        return f"REFUSED: {path!r} has a value not given in the goal. Only open paths whose values you were given."
    url = path_url(path, base)
    if url is None or not host_allowed(url):
        return f"REFUSED: {path!r} is not a path on the allowed site."
    return None


async def open_path(st: AgentState, path: str) -> str:
    """Go straight to a path on the allowed site (a sitemap path too), then a fresh look."""
    args: dict[str, object] = {"path": path}
    refused = _stopped(st) or open_path_refusal(path, st.given_text, st.cfg, BASE)
    if refused:
        return _record(st, "open_path", args, refused)
    url = path_url(path, BASE)
    return await _perform(st, ("open_path", args), lambda: st.surface.goto(url), None, None)


print("OK OFFLINE 18")


# %% OFFLINE 18t: tests for scroll, select_option, open_path
_URL18 = "https://parabank.parasoft.com/parabank/overview.htm"


class _NavSurface(FakeSurface):
    """TEST ONLY: records the wheel point too, and whether the site lock was open per action."""
    probe: FakeSiteLock | None = None

    def _open(self) -> None:
        self.opens.append(bool(self.probe and self.probe.open))

    async def wheel(self, dx: int, dy: int, x: int | None = None, y: int | None = None) -> None:
        self._open()
        self._advance(("wheel", dx, dy, x, y))

    async def goto(self, url: str) -> None:
        self._open()
        await super().goto(url)


_DD_BOX = (300, 190, 420, 215)


def _dd_screen(option: str) -> Screen:
    return (render_screen([("From", 100, 210), (option, 300, 210)]),
            items(("From", 100, 190, 160, 215), (option, *_DD_BOX)))


class _DropdownSurface(_NavSurface):
    """TEST ONLY: a FakeDropdown seen through pixels. The screen shows the chosen option."""

    def __init__(self, dd: FakeDropdown, url: str) -> None:
        super().__init__([_dd_screen(o) for o in dd.options], url)
        self.dd, self.stay = dd, True

    async def screenshot(self) -> bytes:
        return self.screens[self.dd.index][0]

    def ocr(self, png: bytes) -> list[tuple[str, Box, float]]:
        return list(next(found for p, found in self.screens if p == png))

    async def click(self, x: int, y: int) -> None:
        self._open()
        self.calls.append(("click", x, y))
        await self.dd.click(x, y)

    async def type(self, text: str) -> None:
        self._open()
        self.calls.append(("type", text))
        await self.dd.type(text)

    async def press(self, key: str) -> None:
        self._open()
        self.calls.append(("press", key))
        await self.dd.press(key)


def _state18(fs: _NavSurface, given: str = "", cfg: DiscoveryConfig = CFG) -> AgentState:
    lock = FakeSiteLock()
    fs.probe, fs.opens = lock, []
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3d_nav_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=cfg, log=EventLog(run), lock=lock,
                      control=FakeControl(), given_text=given, secrets={})


def _lines18(st: AgentState) -> list[dict]:
    return [json.loads(line) for line in st.log.path.read_text().splitlines()]


_A18 = (render_screen([("Accounts", 100, 211), ("Total", 100, 311)]),
        items(("Accounts", 100, 200, 220, 222), ("Total", 100, 300, 170, 322)))
_B18 = (render_screen([(f"Row {i} of the lower page", 100, 40 + i * 50) for i in range(15)], scale=1.2),
        items(("Footer", 100, 400, 200, 422)))   # dense: a scroll must visibly change the screen


async def _test_18_scroll() -> None:
    st = _state18(_NavSurface([_A18, _B18, _B18], _URL18))
    await observe(st)
    old = [e.ref for e in st.look.elements]
    out = await scroll(st, "down")
    assert out.startswith("OK") and "'Footer'" in out, out
    assert st.surface.calls == [("wheel", 0, CFG.scroll_px, None, None)], st.surface.calls
    assert all(e.ref not in old for e in st.look.elements), "new refs after a scroll"
    assert resolve_target(st.look, old[0], None, None, CFG).startswith("STALE")
    assert (await click(st, old[0])).startswith("STALE")
    assert (await scroll(st, "down")).startswith("BOTTOM OF PAGE"), "same screen twice"
    assert (await scroll(st, "up")).startswith("TOP OF PAGE")
    assert st.surface.calls[-1] == ("wheel", 0, -CFG.scroll_px, None, None)
    assert (await scroll(st, "down", x=640, y=400)).startswith("BOTTOM")
    assert st.surface.calls[-1] == ("wheel", 0, CFG.scroll_px, 640, 400), "wheels over the point"
    n = len(st.surface.calls)
    assert (await scroll(st, "down", x=5000, y=10)).startswith("REFUSED")
    assert (await scroll(st, "down", x=10)).startswith("REFUSED")
    assert (await scroll(st, "sideways")).startswith("REFUSED")
    assert len(st.surface.calls) == n, "a refused scroll never touches the mouse"
    assert st.surface.opens == [True] * n and st.lock.windows == n and st.lock.open is False
    assert [e["tool"] for e in _lines18(st)] == ["observe", "scroll", "click"] + ["scroll"] * 6


_OPTS18 = ["12345", "12456", "13344", "13511", "14000"]


async def _test_18_select() -> None:
    st = _state18(_DropdownSurface(FakeDropdown(_OPTS18), _URL18), given="pay from 13344")
    await observe(st)
    dd_ref = fuzzy_find(st.look.elements, "12345").ref
    out = await select_option(st, "13344", ref=dd_ref)
    assert out.startswith("OK") and "'13344'" in out, out
    assert st.surface.calls == [("click", 360, 202), ("type", "13344"), ("press", "Enter")]
    assert st.look.by_ref(dd_ref) is None, "old refs are stale after a select"
    assert st.surface.opens == [True] * 3 and st.lock.windows == 1 and st.lock.open is False
    ev = _lines18(st)[-1]
    assert ev["tool"] == "select_option" and ev["hints"]["text"] == "12345" and ev["crop"]
    st = _state18(_DropdownSurface(FakeDropdown(_OPTS18, typeable=False), _URL18), given="13511")
    await observe(st)
    out = await select_option(st, "13511", x=360, y=202)
    assert out.startswith("OK"), out
    assert st.surface.calls.count(("press", "ArrowDown")) == 3, "ArrowDown fallback"
    cfg = dataclasses.replace(CFG, dropdown_down_limit=2)
    st = _state18(_DropdownSurface(FakeDropdown(_OPTS18, typeable=False), _URL18), "99999", cfg)
    await observe(st)
    out = await select_option(st, "99999", x=360, y=202)
    assert out.startswith("ASK_HUMAN"), out
    assert st.surface.calls.count(("press", "ArrowDown")) == 2, "stops at the limit"
    assert (await select_option(st, "13344", x=360, y=202)).startswith("ASK_HUMAN"), "not in goal"
    assert (await select_option(st, "99999", ref=9999)).startswith("STALE")
    assert st.surface.calls.count(("press", "ArrowDown")) == 2, "refusals touch nothing"
    assert [e["tool"] for e in _lines18(st)] == ["observe"] + ["select_option"] * 3


async def _test_18_open_path() -> None:
    st = _state18(_NavSurface([_A18, _B18, _A18, _B18], _URL18), given="show activity for account 13344")
    await observe(st)
    for bad in ("/parabank/register.htm", "/parabank/ADMIN.htm", "/lookup.htm?x=1"):
        assert (await open_path(st, bad)).startswith("REFUSED"), bad
    out = await open_path(st, "/parabank/activity.htm?id=99999")
    assert out.startswith("REFUSED") and "goal" in out, out
    for off in ("https://evil.com/x.htm", "//evil.com/x.htm", "javascript:alert(1)", "about:blank",
                "javascript://parabank.parasoft.com/%0Aalert(1)"):
        assert (await open_path(st, off)).startswith("REFUSED"), off
    assert open_path_refusal("/x.htm", "", CFG, "https://evil.com/app").startswith("REFUSED"), "host gate"
    assert open_path_refusal("/x.htm", "", CFG, "https://parabank.parasoft.com/parabank") is None
    assert st.surface.calls == [] and st.lock.windows == 0, "refusals never navigate"
    gen = st.look.gen
    out = await open_path(st, "/parabank/activity.htm?id=13344")
    want = "https://parabank.parasoft.com/parabank/activity.htm?id=13344"
    assert st.surface.calls == [("goto", want)], st.surface.calls
    assert out.startswith("OK") and "'Footer'" in out and st.look.gen == gen + 1, out
    assert st.surface.opens == [True] and st.lock.windows == 1 and st.lock.open is False
    page = sitemap_paths(["https://parabank.parasoft.com/parabank/overview.htm"], CFG)[0]
    assert (await open_path(st, page)).startswith("OK"), "a sitemap path opens"
    assert st.surface.calls[-1] == ("goto", _URL18)
    assert (await open_path(st, "/activity.htm?id=13344")).startswith("OK"), "cli.py-style path"
    assert st.surface.calls[-1] == ("goto", want), "joined to the configured base"
    assert [e["tool"] for e in _lines18(st)] == ["observe"] + ["open_path"] * 12


run_sync(_test_18_scroll())
run_sync(_test_18_select())
run_sync(_test_18_open_path())
print("OK OFFLINE 18t")


# %% OFFLINE 19: extract_value (OCR box -> typed, saved value; Q8 table read), finish, business outcome
from cua.recorder import VALUE_TYPES, value_matches_type

FINISH_MARKER = "FINISHED:"
_OUTCOME_RE = re.compile(r"[A-Z][A-Z0-9_]*")


def _squash_ws(s: str) -> str:
    return " ".join(s.split())


def _is_secret(st: AgentState, text: str) -> bool:
    return any(secret_leaked(text, v) for v in st.secrets.values() if v)


def _scrub_secrets(st: AgentState, text: str) -> str:
    """Replace every secret value in free text with its NAME (the value never reaches log or model)."""
    for name, value in st.secrets.items():
        if value:
            text = text.replace(value, f"[secret:{name}]")
    return text


def _is_header(els: Sequence[Element], target: Element) -> bool:
    """Visual D101: `target` is a column header if some cell below it reads as (row, target.text)."""
    below = [e for e in els if e.box.y1 >= target.box.y2 and _x_overlap(e.box, target.box)]
    return any((t := infer_table_cell(els, e.ref)) and t.column == target.text for e in below)


def _extract_refusal(st: AgentState, el: Element, value_type: str) -> str | None:
    if _is_header(st.look.elements, el):
        return (f"REFUSED: [{el.ref}] is a table column header, not a value. "
                "Pick the cell in the row you need, under that header.")
    if value_type not in VALUE_TYPES:
        return f"REFUSED: value_type must be one of {', '.join(VALUE_TYPES)}."
    if not value_matches_type(el.text, value_type):
        return f"REFUSED: the text in [{el.ref}] does not look like a {value_type}."
    return None


async def extract_value(st: AgentState, ref: int, save_as: str, value_type: str,
                        description: str) -> str:
    """Read box [ref] on the latest screen, type-check it and save it as `save_as`. Reading
    never touches the site. The log keeps the name, type and replay hints, never the value."""
    args: dict[str, object] = {"ref": ref, "save_as": save_as, "value_type": value_type,
                               "description": description}
    if st.look is None:
        return _record(st, "extract_value", args, "REFUSED: call observe first")
    el = st.look.by_ref(ref)
    if el is None:
        return _record(st, "extract_value", args, resolve_target(st.look, ref, None, None, st.cfg))
    if _is_secret(st, el.text):     # no shot, crop or hints: they would carry the secret
        return _record(st, "extract_value", args,
                       "REFUSED: that box shows a secret value. Secrets can never be extracted.")
    crop, hints = before_crop(st, el), hints_for(st, el)
    extras = EventExtras(shot_png=st.look.png, crop_png=crop, hints=hints)
    refusal = _extract_refusal(st, el, value_type)
    if refusal:
        return _record(st, "extract_value", args, refusal, extras)
    st.saved[save_as] = el.text.strip()
    logged = f"OK: saved {save_as!r} ({value_type})."
    _record(st, "extract_value", args, logged, extras)
    return f"{logged} Value: {st.saved[save_as]}"


async def finish(st: AgentState, summary: str) -> str:
    """End the run. Start the summary with 'STUCK:' or 'DECLINED:' when that is why it ended."""
    clean = _scrub_secrets(st, summary)
    names = sorted(st.saved)
    _record(st, "finish", {"summary": clean, "saved": names}, FINISH_MARKER)
    shown = ", ".join(f"{k}={st.saved[k]}" for k in names) or "nothing"
    return f"{FINISH_MARKER} {clean} (saved: {shown}). Stop now."


async def finish_business_outcome(st: AgentState, outcome: str, proof_text: str) -> str:
    """End the run as a known business outcome (a bad-input probe). `proof_text` must be on the
    CURRENT screen: it is checked against the joined OCR text, whitespace-normalised."""
    proof = _squash_ws(proof_text)
    args: dict[str, object] = {"outcome": outcome, "proof_text": proof}
    look = await fresh_look(st)
    if not _OUTCOME_RE.fullmatch(outcome):
        result = "REFUSED: outcome must be a short UPPER_SNAKE name, e.g. ACCOUNT_NOT_FOUND."
    elif not proof or _is_secret(st, proof) or proof not in _squash_ws(look.text()):
        result = "REFUSED: that exact text is not on the current screen. Copy it exactly from the screen."
    else:
        extras = EventExtras(shot_png=look.png, extra={"outcome": outcome, "proof": proof})
        _record(st, "finish_business_outcome", args, FINISH_MARKER, extras)
        return f"{FINISH_MARKER} business outcome {outcome} recorded. Stop now."
    return _record(st, "finish_business_outcome", {"outcome": outcome}, result)


print("OK OFFLINE 19")


# %% OFFLINE 19t: tests for extract_value, finish, finish_business_outcome
_URL19 = "https://parabank.parasoft.com/parabank/overview.htm"
_ACC19 = load_ocr_fixture("accounts")
_LONE19 = items(("Balance", 100, 200, 170, 220), ("$100.00", 200, 200, 270, 220))
_ERR19 = items(("Error!", 100, 100, 160, 120), ("Could not find", 100, 150, 220, 170),
               ("account #99999.", 230, 150, 360, 170))


def _state19(found: list, secrets: dict[str, str] | None = None) -> AgentState:
    fs = FakeSurface([(render_screen([("screen", 100, 100)]), list(found))], _URL19)
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3e_extract_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=CFG, log=EventLog(run), lock=FakeSiteLock(),
                      control=FakeControl(), given_text="read the balance of account 20002",
                      secrets=secrets or {})


def _ev19(st: AgentState) -> list[dict]:
    return [json.loads(line) for line in st.log.path.read_text().splitlines()]


def _ref19(st: AgentState, text: str, x1: int) -> int:
    return next(e.ref for e in st.look.elements if e.text == text and e.box.x1 == x1)


async def _test_19_table_read() -> None:
    st = _state19(_ACC19)
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "currency", "The balance.")
    assert out.startswith("OK") and "$100.00" in out, out
    assert st.saved == {"balance": "$100.00"}
    ev = _ev19(st)
    assert len(ev) == 1 and ev[0]["tool"] == "extract_value"
    assert ev[0]["hints"]["table"] == {"row_key": "20002", "column": "Balance"}, ev[0]["hints"]
    assert ev[0]["args"] == {"ref": _ref19(st, "$100.00", 300), "save_as": "balance",
                             "value_type": "currency", "description": "The balance."}
    assert st.surface.calls == [] and st.lock.windows == 0, "reading never touches the site"


async def _test_19_labelled_value() -> None:
    st = _state19(_LONE19)
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "$100.00", 200), "balance", "currency", "The balance.")
    assert out.startswith("OK"), out
    hints = _ev19(st)[0]["hints"]
    assert hints["table"] is None and hints["anchor"]["label"] == "Balance", hints


async def _test_19_refusals() -> None:
    st = _state19(_ACC19)
    await fresh_look(st)
    head = await extract_value(st, _ref19(st, "Balance", 300), "balance", "string", "x")
    assert head.startswith("REFUSED") and "header" in head, head
    bad = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "integer", "x")
    assert bad.startswith("REFUSED") and "integer" in bad, bad
    unknown = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "money", "x")
    assert unknown.startswith("REFUSED"), unknown
    stale = await extract_value(st, 9999, "balance", "currency", "x")
    assert stale.startswith("STALE"), stale
    assert st.saved == {} and len(_ev19(st)) == 4, "every refusal is one log line, nothing saved"
    fresh = _state19(_ACC19)
    assert (await extract_value(fresh, 1, "b", "currency", "x")).startswith("REFUSED"), "no look yet"


async def _test_19_no_secret() -> None:
    st = _state19(_ACC19, secrets={"PARABANK_PASSWORD": "20013"})
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "20013", 100), "acct", "string", "x")
    assert out.startswith("REFUSED") and "20013" not in out, out
    assert st.saved == {}
    assert_no_secret(st.log.run_dir, "20013")


async def _test_19_finish() -> None:
    st = _state19(_ACC19, secrets={"PARABANK_PASSWORD": "hunter2"})
    st.saved["balance"] = "$100.00"
    out = await finish(st, "Read the balance. hunter2")
    assert out.startswith(FINISH_MARKER), out
    assert "hunter2" not in out and "[secret:PARABANK_PASSWORD]" in out, out
    ev = _ev19(st)
    assert len(ev) == 1 and ev[0]["tool"] == "finish" and ev[0]["args"]["saved"] == ["balance"]
    assert_no_secret(st.log.run_dir, "hunter2")


async def _test_19_business_outcome() -> None:
    st = _state19(_ERR19)
    await fresh_look(st)
    ok = await finish_business_outcome(st, "ACCOUNT_NOT_FOUND", "Could not find  account\n#99999.")
    assert ok.startswith(FINISH_MARKER), ok
    ev = _ev19(st)[-1]
    assert ev["args"] == {"outcome": "ACCOUNT_NOT_FOUND", "proof_text": "Could not find account #99999."}
    missing = await finish_business_outcome(st, "ACCOUNT_NOT_FOUND", "Account locked.")
    assert missing.startswith("REFUSED"), missing
    empty = await finish_business_outcome(st, "X", "   ")
    assert empty.startswith("REFUSED"), empty
    assert (await finish_business_outcome(st, "not found", "Error!")).startswith("REFUSED")
    assert len(_ev19(st)) == 4
    unseen = _state19(_ERR19)
    assert (await finish_business_outcome(unseen, "X", "Error!")).startswith(FINISH_MARKER), \
        "no look yet -> takes one first"


assert value_matches_type("$100.00", "currency") and not value_matches_type("$100.00", "integer")
run_sync(_test_19_table_read())
run_sync(_test_19_labelled_value())
run_sync(_test_19_refusals())
run_sync(_test_19_no_secret())
run_sync(_test_19_finish())
run_sync(_test_19_business_outcome())
print("OK OFFLINE 19t")


# %% OFFLINE 20: human tools (ask_human, request_value, request_missing_values, take_over; Q21)
import time as _h20_time

_H20_STUCK_HEADS = ("NO CHANGE", "STUCK:", "STOP:")
_H20_QUIET_TOOLS = frozenset({"observe", "human_approval"})   # never decide "stuck" on these


def _human_has_control(st: AgentState) -> bool:
    """True only while a take over is in progress (the human holds the live session)."""
    return bool(getattr(st, "_h20_human", False))


def _h20_on_start_page(st: AgentState) -> bool:
    return st.page() in st.cfg.start_pages


def _h20_start_refusal(tool: str) -> str:
    return (f"REFUSED: never {tool} on the start page. First open the page where the task is "
            "done, then ask.")


async def ask_human(st: AgentState, question: str) -> str:
    """A question only (not a value). The human answers in the control window, never on the site.
    Secret values are scrubbed from both the log and what the model gets back."""
    q = _scrub_secrets(st, question)
    if _h20_on_start_page(st):
        return _record(st, "ask_human", {"question": q}, _h20_start_refusal("ask a human"))
    answer = _scrub_secrets(st, (await st.control.ask_text(question)).strip())
    result = answer or "DECLINED: the human gave no answer."
    return _record(st, "ask_human", {"question": q}, result, EventExtras(human_entry=True))


def _h20_filled(st: AgentState, target: Element | Point, label: str) -> bool:
    """Does the box already show text (other than its own label / placeholder)?"""
    if isinstance(target, Element):
        return normalise(target.text) != normalise(label)
    read = [e.text for e in st.look.elements
            if _contains(crop_box_for(target, st.cfg), e.box.center)
            and normalise(e.text) != normalise(label)]
    return bool(" ".join(read).strip())


def _h20_job(st: AgentState, tool: str, point: Point, target: Element | Point,
             args: dict[str, object]) -> _TypeJob:
    """A human-value typing job (p3c's _TypeJob): crop + hints from the look BEFORE typing."""
    return _TypeJob(tool, args, point, crop_box_for(target, st.cfg), before_crop(st, target),
                    hints_for(st, target), human=True)


async def request_value(st: AgentState, label: str, ref: int | None = None, x: int | None = None,
                        y: int | None = None) -> str:
    """Ask a human for ONE field's value; our code types it (p3c's _run_job, human_entry=true).
    The value never reaches the log or the model: only OK / SKIP / DECLINED comes back."""
    where = _where(ref, x, y)
    if _h20_on_start_page(st):
        return _record(st, "request_value", {"hint": label, **where},
                       _h20_start_refusal("ask for a value"))
    got = _type_target(st, ref, x, y)
    if isinstance(got, str):
        return _record(st, "request_value", {"hint": label, **where}, got)
    point, target = got
    field_label = _field_label(st, target)
    args: dict[str, object] = {"field": field_label, "hint": label, **where}
    if _h20_filled(st, target, field_label):
        return _record(st, "request_value", args, f"SKIP: {field_label!r} is already filled.")
    job = _h20_job(st, "request_value", point, target, args)
    given = await st.control.ask_value(field_label, job.crop, masked=_sensitive(st, field_label))
    if not given:
        return _record(st, "request_value", args, f"DECLINED: no value was given for {field_label!r}.",
                       EventExtras(crop_png=job.crop, hints=job.hints, human_entry=True))
    return await _run_job(st, job, given)


def _h20_plan(st: AgentState, fields: list[dict]) -> list[tuple[str, _TypeJob | str]]:
    """Per field, on ONE look: (label, a typing job) or (label, its SKIP / REFUSED line)."""
    plan: list[tuple[str, _TypeJob | str]] = []
    for f in fields:
        hint = str(f.get("hint") or "")
        x, y = f.get("x"), f.get("y")
        got = _type_target(st, None, x if isinstance(x, int) else None, y if isinstance(y, int) else None)
        if isinstance(got, str):
            plan.append((hint or "field", got))
            continue
        point, target = got
        label = _field_label(st, target)
        if _h20_filled(st, target, label):
            plan.append((label, f"SKIP: {label!r} is already filled."))
            continue
        args: dict[str, object] = {"field": label, "hint": hint, "x": point.x, "y": point.y}
        plan.append((label, _h20_job(st, "request_missing_values", point, target, args)))
    return plan


async def _h20_fill(st: AgentState, label: str, job: _TypeJob, given: str | None) -> str:
    if not given:
        _record(st, "request_missing_values", job.args, f"DECLINED: no value for {label!r}.",
                EventExtras(crop_png=job.crop, hints=job.hints, human_entry=True))
        return f"{label}: DECLINED"
    return f"{label}: " + (await _run_job(st, job, given)).split("\n", 1)[0]


def _h20_hiding_ocr(ocr: OcrEngine, boxes: list[Box]) -> OcrEngine:
    """OCR that never reports text inside a box a human already filled (so a later field's
    re-read, logged by _run_job, cannot carry an earlier human value)."""
    def read(png: bytes) -> list[tuple[str, Box, float]]:
        return [it for it in ocr(png) if not any(_contains(b, it[1].center) for b in boxes)]
    return read


async def _h20_fill_all(st: AgentState, plan: list[tuple[str, _TypeJob | str]],
                        answers: dict[int, str | None]) -> list[str]:
    real_ocr, done = st.ocr, []
    lines = []
    try:
        for label, job in plan:
            if isinstance(job, str):
                lines.append(f"{label}: {job}")
                continue
            lines.append(await _h20_fill(st, label, job, answers[id(job)]))
            done.append(job.box)
            st.ocr = _h20_hiding_ocr(real_ocr, done)
    finally:
        st.ocr = real_ocr
    for box in done:
        _scrub_box(st, box)
    return lines


async def request_missing_values(st: AgentState, fields: list[dict]) -> str:
    """Every empty field on this page, in ONE control-window ask; our code types each answer.
    Returns one line per field (OK / SKIP / DECLINED / REFUSED), then the new screen."""
    if _h20_on_start_page(st):
        return _record(st, "request_missing_values", {"count": len(fields)},
                       _h20_start_refusal("ask for values"))
    if st.look is None or not fields:
        return _record(st, "request_missing_values", {"count": len(fields)},
                       "REFUSED: call observe first, and list at least one field")
    plan = _h20_plan(st, fields)
    asks = [(label, job) for label, job in plan if isinstance(job, _TypeJob)]
    given = await st.control.ask_values([lb for lb, _ in asks], [j.crop for _, j in asks]) if asks else []
    answers = {id(job): value for (_, job), value in zip(asks, given, strict=True)}
    lines = await _h20_fill_all(st, plan, answers)
    return "\n".join(lines) + f"\nNew screen (gen {st.look.gen}, page {st.page()}):\n" + \
        format_elements(st.look.elements)


def _h20_last_result(st: AgentState) -> str:
    """The latest logged tool result that is not a plain look or an approval record."""
    if not st.log.path.exists():
        return ""
    for line in reversed(st.log.path.read_text(encoding="utf-8").splitlines()):
        ev = json.loads(line)
        if ev["tool"] not in _H20_QUIET_TOOLS:
            return str(ev["result"])
    return ""


def _h20_is_stuck(st: AgentState) -> bool:
    """Q21: take over only when stuck: a stuck flag, or the last action had no effect / stopped."""
    return bool(getattr(st, "stuck", False)) or _h20_last_result(st).startswith(_H20_STUCK_HEADS)


def _h20_save_after(st: AgentState, png: bytes) -> str:
    """The AFTER screenshot, named after the step the human_takeover event is about to get."""
    rel = f"shots/{st.log.step + 1:03d}_after.png"
    (st.log.run_dir / rel).write_bytes(png)
    return rel


async def _h20_hand_over(st: AgentState, reason: str) -> None:
    """Unlock for the human, wait for Done, then RE-LOCK FIRST; the flag is cleared only after."""
    st._h20_human = True                     # AgentState is not frozen (a new attribute, Q21)
    try:
        await st.lock.unlock()
        try:
            await st.control.take_over(reason)
        finally:
            await st.lock.lock()
    finally:
        st._h20_human = False


async def take_over(st: AgentState, reason: str) -> str:
    """Q21: hand the live session to a human, ONLY when stuck. No typed value is ever captured:
    the event is human_entry=true, recordable=false. Returns the fresh screen after Done."""
    why = _scrub_secrets(st, reason)
    if not _h20_is_stuck(st):
        return _record(st, "take_over", {"reason": why},
                       "REFUSED: not stuck. Use take_over only after an action had no effect.")
    before = st.look.png if st.look else await st.surface.screenshot()
    url_before, t0 = st.surface.url, _h20_time.monotonic()
    await _h20_hand_over(st, why)
    look = await fresh_look(st)
    extra: dict[str, object] = {
        "reason": why, "url_before": url_before, "url_after": st.surface.url,
        "shot_after": _h20_save_after(st, look.png), "recordable": False, "take_over": True,
        "duration_s": round(_h20_time.monotonic() - t0, 3)}
    text = f"OK: the human handed back.\nNew screen (gen {look.gen}, page {st.page()}):\n" + \
        format_elements(look.elements)
    return _record(st, "human_takeover", {"reason": why}, text,
                   EventExtras(shot_png=before, human_entry=True, extra=extra))


class FakeControlTO(FakeControl):
    """TEST ONLY. FakeControl + take_over: records the lock state at start, runs an optional
    `during` coroutine (the human on the site), then returns (the Done click)."""

    def __init__(self, *args: object, during: Callable[[], Awaitable[None]] | None = None,
                 lock: FakeSiteLock | None = None, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.during, self.lock = during, lock
        self.lock_seen: list[bool] = []

    async def take_over(self, reason: str) -> None:
        self.prompts.append(("take_over", reason))
        self.lock_seen.append(bool(self.lock and self.lock.open))
        if self.during is not None:
            await self.during()


_H20_TO_PANE = ('<div id="takeoverPane" class="pane"><div id="who">In control: human</div>'
                '<button id="doneBtn">Done</button></div>')
_H20_TO_JS = "$('doneBtn').onclick = () => send({done: true});\n"


def control_html_to() -> str:
    """control_html() + a Take over pane (who is in control + Done). Text set via textContent only."""
    html = control_html().replace("</body>", "")
    html = html.replace('<div id="textPane"', _H20_TO_PANE + '<div id="textPane"', 1)
    return html.replace("</script>", _H20_TO_JS + "</script></body>", 1)


class BrowserControlWindowTO(BrowserControlWindow):
    """BrowserControlWindow + take_over (Q21), on the same unique-id `_ask` mechanism."""

    async def setup(self) -> None:
        await self._page.expose_function("cuaReply", self._on_reply)
        self._page.on("close", self._on_close)
        await self._page.set_content(control_html_to())

    async def take_over(self, reason: str) -> None:
        await self.status("In control: HUMAN")
        await self._ask({"mode": "takeover", "title": "Take over: you are in control",
                         "details": f"{reason} Work on the site window, then click Done to hand "
                                    "back.", "image": None})
        await self.status("In control: agent")


print("OK OFFLINE 20")


# %% OFFLINE 20t: tests for the human tools (fake control, fake lock, a FAKE secret; no browser)
_URL20 = "https://parabank.parasoft.com/parabank/billpay.htm"
_URL20_START = "https://parabank.parasoft.com/parabank/overview.htm"
_ROWS20 = {"Phone": 216, "City": 276, "Zip": 336}
_SECRET20 = "hunter2-fake"


def _screen20(shown: dict[str, str]) -> Screen:
    """One label + input box per _ROWS20 row; `shown` = what a box displays."""
    labels, found, rects = [], [], []
    for name, y in _ROWS20.items():
        labels.append((name, 100, y))
        found.append((name, 100, y - 16, 200, y + 6))
        rects.append(Box(250, y - 21, 450, y + 9))
        if name in shown:
            labels.append((shown[name], 260, y))
            found.append((shown[name], 260, y - 16, 440, y + 6))
    return render_screen(labels, rects), items(*found)


class _OrderLock(FakeSiteLock):
    """TEST ONLY: FakeSiteLock that appends lock / unlock to a shared order list."""
    def __init__(self, order: list[str]) -> None:
        super().__init__()
        self.order = order

    async def lock(self) -> None:
        self.order.append("lock")
        await super().lock()

    async def unlock(self) -> None:
        self.order.append("unlock")
        await super().unlock()


class _OrderSurface(FakeSurface):
    order: list[str] = []

    async def screenshot(self) -> bytes:
        self.order.append("shot")
        return await super().screenshot()


def _state20(screens: list[Screen], url: str = _URL20, values: list[str | None] = (),
             texts: list[str] = ()) -> AgentState:
    order: list[str] = []
    fs = _OrderSurface(list(screens), url)
    fs.order = order
    lock = _OrderLock(order)
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3f_human_"))
    control = FakeControlTO(values=list(values), texts=list(texts), lock=lock)
    return AgentState(surface=fs, ocr=fs.ocr, cfg=CFG, log=EventLog(run), lock=lock,
                      control=control, given_text="pay a bill", secrets={"password": _SECRET20})


def _pt20(name: str) -> tuple[int, int]:
    return 350, _ROWS20[name] - 6



def _ev20(st: AgentState) -> list[dict]:
    return [json.loads(line) for line in st.log.path.read_text().splitlines()]


async def _test_20_takeover_refused() -> None:
    st = _state20([_screen20({})])
    await observe(st)
    out = await take_over(st, "an odd popup")
    assert out.startswith("REFUSED: not stuck"), out
    assert "unlock" not in st.lock.order and st.control.prompts == [], "never unlocked"
    assert not _human_has_control(st)


async def _test_20_takeover_stuck() -> None:
    st = _state20([_screen20({}), _screen20({"Phone": "5550199"})])
    await observe(st)
    _record(st, "click", {"ref": 1}, "NO CHANGE: the screen looks the same after that action.")
    seen: list[bool] = []

    async def human_on_site() -> None:
        seen.append(_human_has_control(st))
        st.lock.order.append("human")
        st.surface._i, st.surface.url = 1, _URL20 + "?done"
    st.control.during = human_on_site
    st.lock.order.clear()
    out = await take_over(st, f"a CAPTCHA; password {_SECRET20} did not help")
    assert out.startswith("OK: the human handed back"), out
    assert st.lock.order == ["unlock", "human", "lock", "shot"], st.lock.order
    assert st.control.lock_seen == [True] and seen == [True], "unlocked only while the human works"
    assert st.lock.open is False and not _human_has_control(st)
    ev = _ev20(st)[-1]
    assert ev["tool"] == "human_takeover" and ev["human_entry"] is True
    x = ev["extra"]
    assert x["recordable"] is False and x["url_before"] == _URL20 and x["url_after"] == _URL20 + "?done"
    assert x["duration_s"] >= 0 and (st.log.run_dir / x["shot_after"]).is_file() and ev["shot"]
    assert "[secret:password]" in x["reason"]
    assert_no_secret(st.log.run_dir, _SECRET20)
    assert all(_SECRET20 not in p for _, p in st.control.prompts)


async def _test_20_request_value() -> None:
    x, y = _pt20("Phone")
    st = _state20([_screen20({"Phone": "5550100"})], values=["never"])
    await observe(st)
    assert (await request_value(st, "Phone", x=x, y=y)).startswith("SKIP"), "already filled"
    assert st.control.prompts == [] and st.surface.calls == []
    st = _state20([_screen20({})], values=[None])
    await observe(st)
    assert (await request_value(st, "Phone", x=x, y=y)).startswith("DECLINED")
    assert st.surface.calls == [] and st.lock.windows == 0
    st = _state20([_screen20({}), _screen20({"Phone": "5550199"})], values=["5550199"])
    await observe(st)
    out = await request_value(st, "Phone", x=x, y=y)
    assert out.startswith("OK") and "5550199" not in out, out
    assert st.control.prompts == [("value", "Phone")]
    assert [c[1] for c in st.surface.calls if c[0] == "type"] == ["5550199"]
    ev = _ev20(st)[-1]
    assert ev["tool"] == "request_value" and ev["human_entry"] is True and ev["args"]["field"] == "Phone"
    assert_no_secret(st.log.run_dir, "5550199")


async def _test_20_start_page() -> None:
    st = _state20([_screen20({})], url=_URL20_START, texts=["savings"], values=["v"])
    await observe(st)
    assert (await ask_human(st, "Which account?")).startswith("REFUSED")
    assert (await request_value(st, "Phone", x=350, y=210)).startswith("REFUSED")
    assert (await request_missing_values(st, [{"x": 350, "y": 210, "hint": "Phone"}])).startswith("REFUSED")
    assert st.control.prompts == []
    st = _state20([_screen20({})], texts=["savings"])
    await observe(st)
    assert await ask_human(st, f"Use {_SECRET20}?") == "savings"
    assert_no_secret(st.log.run_dir, _SECRET20)


async def _test_20_missing_values() -> None:
    e, p, pc = _screen20({}), _screen20({"Phone": "5550199"}), _screen20({"Phone": "5550199", "City": "Springfield"})
    st = _state20([e, p, p, p, pc, pc, pc], values=["5550199", "Springfield", None])
    await observe(st)
    fields = [{"x": _pt20(n)[0], "y": _pt20(n)[1], "hint": n} for n in _ROWS20]
    out = await request_missing_values(st, fields)
    lines = out.split("\n")
    assert [ln.split(":")[0] for ln in lines[:3]] == ["Phone", "City", "Zip"], out
    assert lines[0].startswith("Phone: OK") and lines[1].startswith("City: OK"), out
    assert lines[2] == "Zip: DECLINED" and lines[3].startswith("New screen"), out
    assert [k for k, _ in st.control.prompts] == ["values"], "ONE ask for every field"
    for v in ("5550199", "Springfield"):
        assert v not in out
        assert_no_secret(st.log.run_dir, v)


async def _test_20_browser_takeover() -> None:
    page = FakeControlPage(lambda p: {"done": True} if p["mode"] == "takeover" else _human(p))
    win = BrowserControlWindowTO(page)
    await win.setup()
    html = page.html
    assert "doneBtn" in html and "takeoverPane" in html and "In control" in html
    assert "http" not in html.casefold() and "innerHTML" not in html
    assert await win.ask_text("q?") == "the answer", "the base asks still work"
    await win.take_over("a popup")
    modes = [p["mode"] for p in page.payloads]
    assert modes[-3:] == ["status", "takeover", "status"], modes
    assert page.payloads[-3]["status"].endswith("HUMAN") and page.payloads[-1]["status"].endswith("agent")


for _t20 in (_test_20_browser_takeover, _test_20_takeover_refused, _test_20_takeover_stuck, _test_20_request_value,
             _test_20_start_page, _test_20_missing_values):
    run_sync(_t20())
_names20 = ("ask_human", "request_value", "request_missing_values", "take_over")
assert all(asyncio.iscoroutinefunction(globals()[n]) for n in _names20)   # what p3b's _free_tool needs
print("OK OFFLINE 20t")


# %% OFFLINE 21: LangChain tool wrappers (one call at a time) + the pure-visual guard
import ast
import functools
import inspect as _inspect

from langchain.tools import tool

HUMAN_HAS_CONTROL = "REFUSED: human has control. Wait until they click Done, then call observe."

_TOOL_DOCS: dict[str, str] = {
    "observe": """Look at the screen: a fresh screenshot, read by OCR, with numbered text boxes.

Returns:
    Each numbered text with its box. Numbers change after every action; use the latest list.
""",
    "click": """Click the text box with this number on the latest screen.

Every click needs a human's Approve unless it is on the safe list; the system asks by itself.

Args:
    ref: Number of the text box on the latest screen.

Returns:
    The new screen, or REFUSED / STALE / DECLINED / NO CHANGE. After DECLINED, never retry.
""",
    "click_at": """Click a point that has no text (an empty input box, an icon, a checkbox).

Args:
    x: Pixels from the left edge of the screenshot.
    y: Pixels from the top edge of the screenshot.

Returns:
    The new screen, or NO CHANGE if nothing happened.
""",
    "type_text": """Type a value into a box, given by number or by point (empty boxes have no number).

Only values from the goal are typed; any other value goes to a human.

Args:
    value: The exact text to type, copied from the goal.
    ref: Number of the box, if it shows text.
    x: Point of an empty box, pixels from the left.
    y: Point of an empty box, pixels from the top.

Returns:
    The new screen, or a refusal. A human-entered value is never shown to you.
""",
    "type_secret": """Type a stored secret by its NAME. You never see the value.

Args:
    name: The secret's name, e.g. username or password.
    ref: Number of the box, if it shows text.
    x: Point of an empty box, pixels from the left.
    y: Point of an empty box, pixels from the top.

Returns:
    OK with the new screen, or REFUSED / STOP.
""",
    "scroll": """Scroll to see things that are not on the screen. Old numbers go stale.

Args:
    direction: up or down.
    x: Optional point over a scrolling panel, pixels from the left.
    y: Optional point over a scrolling panel, pixels from the top.

Returns:
    The new screen with new numbers, or TOP / BOTTOM OF PAGE.
""",
    "select_option": """Pick an option in a dropdown, by the dropdown's number or point.

Args:
    option: The option text, copied from the goal.
    ref: Number of the dropdown.
    x: Point of the dropdown, pixels from the left.
    y: Point of the dropdown, pixels from the top.

Returns:
    The new screen, or ASK_HUMAN when the option is not in the goal or could not be chosen.
""",
    "open_path": """Open a page on the allowed site directly, e.g. /overview.htm.

Args:
    path: A path starting with /. Query values must come from the goal.

Returns:
    The new screen, or REFUSED.
""",
    "extract_value": """Save a value you can see (a balance, a confirmation number).

Args:
    ref: Number of the value's text box (the value itself, never a column header).
    save_as: A short snake_case name for the value.
    value_type: One of string, integer, number, currency, date.
    description: One sentence on what the value is.

Returns:
    OK with the saved value, or REFUSED.
""",
    "finish": """End the run. Log out first.

Args:
    summary: What happened. Start with STUCK: or DECLINED: when that is why the run ended.

Returns:
    FINISHED. Stop after this.
""",
    "finish_business_outcome": """End the run as a known business outcome shown on the screen.

Args:
    outcome: A short UPPER_SNAKE name, e.g. ACCOUNT_NOT_FOUND.
    proof_text: The exact message text copied from the current screen.

Returns:
    FINISHED, or REFUSED if the text is not on the screen.
""",
    "ask_human": """Ask a human a question in the control window. Not for missing values.

Args:
    question: One short question.

Returns:
    The human's typed answer. The human never touches the site.
""",
    "request_value": """Ask a human for ONE field's value; our code types it in.

Args:
    label: The field's name as you read it on the screen.
    ref: Number of the field, if it shows text.
    x: Point of an empty field, pixels from the left.
    y: Point of an empty field, pixels from the top.

Returns:
    OK (the value is never shown to you), SKIP if already filled, or DECLINED.
""",
    "request_missing_values": """Ask a human for EVERY empty field on this page, in one go.

Args:
    fields: One entry per empty field: its point (x, y) and your label for it (hint).

Returns:
    One line per field: OK, SKIP or DECLINED, then the new screen. Values are never shown.
""",
    "take_over": """Hand the live session to a human. ONLY when truly stuck: the last action had
no effect and no other tool can express what is needed (an odd popup, a CAPTCHA).

Args:
    reason: What blocks you, in one sentence.

Returns:
    REFUSED if you are not stuck, or the fresh screen after the human clicks Done.
""",
}

TOOL_NAMES = frozenset(_TOOL_DOCS)


def _free_tool(name: str) -> Callable[..., Awaitable[str]]:
    """The free `async def name(st, ...)` tool from the cells above, found by name."""
    fn = globals()[name]
    assert _inspect.iscoroutinefunction(fn), name
    return fn


def _as_tool(st: AgentState, name: str, gate: asyncio.Lock) -> object:
    """One LangChain tool over the free function `name`, with `st` bound and the model-facing
    docstring. Refused while a human holds control; otherwise one call at a time (`gate`)."""
    fn = _free_tool(name)
    params = list(_inspect.signature(fn).parameters.values())[1:]   # drop `st`

    async def wrapper(**kwargs: object) -> str:
        if _human_has_control(st):
            return HUMAN_HAS_CONTROL
        async with gate:
            if _human_has_control(st):
                return HUMAN_HAS_CONTROL
            return await fn(st, **kwargs)

    wrapper.__name__ = wrapper.__qualname__ = name
    wrapper.__doc__ = _TOOL_DOCS[name]
    wrapper.__signature__ = _inspect.Signature(params, return_annotation=str)
    wrapper.__annotations__ = {p.name: p.annotation for p in params} | {"return": str}
    return tool(parse_docstring=True)(wrapper)


def build_tools(st: AgentState) -> list:
    """Every free tool as a LangChain tool over `st`, one call at a time.

    The per-call gate is its OWN lock, not st.act_lock: act() already takes st.act_lock around
    each site action, and asyncio.Lock is not re-entrant, so reusing it here would deadlock.
    (cua.agent's `one_at_a_time` is a closure inside DiscoveryAgent.build_tools, so it cannot be
    imported; this is the same pattern: one lock around the whole tool call.)"""
    gate = asyncio.Lock()
    return [_as_tool(st, name, gate) for name in _TOOL_DOCS]


print("OK OFFLINE 21")


# %% OFFLINE 22: the visual system prompt + the optional TypeSafe middleware
from cua.agent import JOB_EXTRA_TOOLS, NEVER_HIDE, build_langchain_agent, build_typesafe_middleware  # noqa: F401

VISUAL_SYSTEM_PROMPT = """You are an expert browser operator on a banking demo site. You see the screen ONLY as a picture read by OCR: every tool result lists numbered text boxes with their positions. You act only with the mouse and keyboard, through these tools.

## Tools
- observe: take a fresh look. Call it first, and again whenever you are unsure.
- click(ref): click a numbered text (a button, a link, a menu item).
- click_at(x, y): click a point with NO text: an empty input box, an icon, a checkbox. Empty boxes have no number, so point at them.
- type_text(value, ref or x,y): type a value from the goal into a box. Empty boxes: give the point.
- type_secret(name, ref or x,y): type a stored secret by NAME (username, password). You never see the value.
- scroll(direction): for things you cannot see. Old numbers go stale; use the new ones.
- select_option(option, ref or x,y): pick a dropdown option from the goal.
- open_path(path): open a page on the site directly.
- extract_value(ref, save_as, value_type, description): save a value you need (a balance). Point at the value, never at its column header.
- request_value(label, ref or x,y): ask a human for ONE field's value; our code types it.
- request_missing_values(fields): ask a human for EVERY empty field on this page at once.
- ask_human(question): a question only, when unsure what to do. Not for missing values.
- take_over(reason): ONLY when truly stuck: the last action had no effect and no other tool can do what is needed. A human then works on the live page and hands back.
- finish(summary): end the run. finish_business_outcome(outcome, proof_text): end on a known message shown on the screen.

## How to work
1. Call observe first. If you see a login form, log in with type_secret at the boxes' points, then confirm the account page appears.
2. Refer to things only by the LATEST numbers, or by points on the latest screenshot. Numbers change after every action.
3. Use ONLY values from the goal. Never invent one. If values are missing, FIRST open the page where the task is done, THEN call request_missing_values ONCE. Never ask a human on the start page.
4. If a result says a human entered a value, do not type it again.
5. Every click that is not on the safe list asks a human by itself. If a result says DECLINED, never retry or work around it: log out, then finish with 'DECLINED:'.
6. Make ONE tool call at a time.
7. If you repeat the same action 3 times or are lost, log out and finish with 'STUCK:'. Use take_over only when truly stuck, never for a risky click.
8. Attempt login at most 3 times. If the login could not be verified, stop: finish with 'STUCK:'.
9. Always log out before you finish: happy path, STUCK or DECLINED. Do not leave the session open.
"""

VISUAL_EXTRA_NEVER_HIDE = frozenset({
    "click_at", "type_text", "select_option", "scroll", "extract_value", "open_path",
    "finish_business_outcome", "request_missing_values", "request_value", "ask_human", "take_over"})


class _UrlView:
    """What build_typesafe_middleware reads from its `agent` argument: `agent.page.url`."""

    def __init__(self, st: AgentState) -> None:
        self.page = st.surface


def build_middleware(st: AgentState) -> list:
    """The TypeSafe tool router + model router (D50/D52), or [] with no TYPESAFE_API_KEY.
    Its fast/powerful models are `cua.models.make_chat_model("haiku"/"sonnet")` (Iliad gateway)."""
    return build_typesafe_middleware(_UrlView(st), extra_never_hide=set(VISUAL_EXTRA_NEVER_HIDE))


print("OK OFFLINE 22")


# %% OFFLINE 21t: tests for OFFLINE 21 (tool set, one-at-a-time, human control, no secret params,
# the pure-visual guard M1, and the cross-part name-collision guard)
import re as _re21

_ARGS21: dict[str, dict] = {
    "observe": {}, "click": {"ref": 1}, "click_at": {"x": 1, "y": 1},
    "type_text": {"value": "a", "ref": 1}, "type_secret": {"name": "password", "ref": 1},
    "scroll": {"direction": "down"}, "select_option": {"option": "a", "ref": 1},
    "open_path": {"path": "/x.htm"},
    "extract_value": {"ref": 1, "save_as": "a", "value_type": "string", "description": "d"},
    "finish": {"summary": "s"}, "finish_business_outcome": {"outcome": "A", "proof_text": "p"},
    "ask_human": {"question": "q"}, "request_value": {"label": "l", "ref": 1},
    "request_missing_values": {"fields": []}, "take_over": {"reason": "r"},
}
_SECRETISH21 = _re21.compile(r"secret|password|passwd|pwd", _re21.IGNORECASE)


class _SlowSurface21(FakeSurface):
    """TEST ONLY: a slow screenshot that records (start, end) times, to see overlapping calls."""
    spans: list[tuple[float, float]] = []

    async def screenshot(self) -> bytes:
        t0 = time.monotonic()
        await asyncio.sleep(0.05)
        self.spans.append((t0, time.monotonic()))
        return await super().screenshot()


def _state21(surface: FakeSurface | None = None) -> AgentState:
    st = _state16([_S1, _S2])
    st.control = FakeControlTO()
    if surface is not None:
        st.surface, st.ocr = surface, surface.ocr
    return st


def _test_21_names_and_params() -> None:
    tools = build_tools(_state21())
    assert len(TOOL_NAMES) == 15 and {t.name for t in tools} == set(TOOL_NAMES)
    assert set(_ARGS21) == set(TOOL_NAMES)
    for t in tools:
        bad = [p for p in t.args if _SECRETISH21.search(p)]
        assert not bad, (t.name, bad)          # a secret VALUE is never a tool parameter
    ts = next(t for t in tools if t.name == "type_secret")
    assert "name" in ts.args and "value" not in ts.args, ts.args


async def _test_21_one_at_a_time() -> None:
    slow = _SlowSurface21([_S1, _S2], _URL16)
    slow.spans = []
    st = _state21(slow)
    obs = next(t for t in build_tools(st) if t.name == "observe")
    outs = await asyncio.gather(obs.ainvoke({}), obs.ainvoke({}))
    assert all(o.startswith("Screen gen") for o in outs), outs
    (a0, a1), (b0, b1) = sorted(slow.spans)
    assert a1 <= b0, f"two tool calls overlapped: {slow.spans}"


async def _test_21_human_has_control() -> None:
    st = _state21()
    tools = build_tools(st)
    st._h20_human = True
    for t in tools:
        assert await t.ainvoke(_ARGS21[t.name]) == HUMAN_HAS_CONTROL, t.name
    assert st.surface.calls == [] and st.control.prompts == [] and st.look is None
    assert not st.log.path.exists() or st.log.path.read_text() == ""
    st._h20_human = False
    assert (await tools[0].ainvoke({})).startswith("Screen gen")


_test_21_names_and_params()
run_sync(_test_21_one_at_a_time())
run_sync(_test_21_human_has_control())

# --- M1 pure-visual guard: no DOM/JS call on the site anywhere in the parts. -------------------
# Exclusions (by exact name, nothing else): the control window is OUR OWN local page, not the site,
# so it may use evaluate/expose_function/set_content:
#   BrowserControlWindow, BrowserControlWindowTO, FakeControlPage, control_html, control_html_to.
# `.content` as a plain attribute (a LangChain message's `m.content`) is not a call and not flagged.
_M1_EXCLUDED = frozenset({"BrowserControlWindow", "BrowserControlWindowTO", "FakeControlPage",
                          "control_html", "control_html_to"})
_AST_FLAGS = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT | ast.PyCF_ONLY_AST


def _part_sources() -> dict[str, str]:
    paths = sorted((HERE / "parts").glob("p[0-6]*.py"))
    assert len(paths) >= 12, paths
    return {p.name: p.read_text() for p in paths}


def _forbidden_attr(attr: str) -> bool:
    return any(attr == f or (f.endswith("_") and attr.startswith(f)) or attr.startswith(f + "_")
               for f in FORBIDDEN_ON_SITE)


def m1_hits(sources: dict[str, str]) -> list[str]:
    """Every `x.<forbidden>(...)` call (and any `.accessibility` access) outside the excluded
    control-window classes/functions, as 'file:line attr'."""
    hits: list[str] = []
    for fname, src in sources.items():
        tree = compile(src, fname, "exec", flags=_AST_FLAGS)
        skip = {id(n) for d in ast.walk(tree) if getattr(d, "name", None) in _M1_EXCLUDED
                and isinstance(d, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                for n in ast.walk(d)}
        for n in ast.walk(tree):
            if id(n) in skip:
                continue
            called = isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            attr = n.func.attr if called else getattr(n, "attr", None) if isinstance(n, ast.Attribute) else None
            if attr and (_forbidden_attr(attr) if called else attr == "accessibility"):
                hits.append(f"{fname}:{n.lineno} {attr}")
    return hits


# --- name-collision guard: one notebook namespace, so a later part must not silently rebind. ---
_SCRATCH_OK = frozenset({"_png", "_els", "_found", "_ocr", "_shape", "_first", "_k", "_v", "_w",
                         "_texts", "START_URL", "tempfile", "async_playwright"})


def _top_level_names(tree: ast.Module) -> set[str]:
    """Names bound by top-level def/class/assignment (compound statements included, not bodies of
    functions or classes; imports excluded)."""
    names: set[str] = set()
    todo = list(tree.body)
    while todo:
        n = todo.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            names |= {m.id for t in targets for m in ast.walk(t) if isinstance(m, ast.Name)}
        elif isinstance(n, (ast.If, ast.Try, ast.With, ast.AsyncWith, ast.For, ast.AsyncFor)):
            todo += [*n.body, *getattr(n, "orelse", []), *getattr(n, "finalbody", [])]
            todo += [s for h in getattr(n, "handlers", []) for s in h.body]
    return names


def collisions(sources: dict[str, str]) -> dict[str, list[str]]:
    """name -> the parts that define it, for every name defined in 2+ parts (minus _SCRATCH_OK)."""
    where: dict[str, list[str]] = {}
    for fname, src in sources.items():
        for name in _top_level_names(compile(src, fname, "exec", flags=_AST_FLAGS)):
            where.setdefault(name, []).append(fname)
    return {k: v for k, v in where.items() if len(v) > 1 and k not in _SCRATCH_OK}


_parts21 = _part_sources()
assert m1_hits({"bad.py": "async def f(page):\n    await page.evaluate('1')\n"}) == ["bad.py:2 evaluate"]
assert m1_hits({"bad.py": "x = page.get_by_role('button')\n"}) == ["bad.py:1 get_by_role"]
assert m1_hits({"ok.py": "class FakeControlPage:\n    def f(self, p):\n        p.evaluate('1')\n"}) == []
assert m1_hits({"ok.py": "t = m.content\nawait page.mouse.click(1, 2)\nawait page.keyboard.type('a')\n"}) == []
assert not m1_hits(_parts21), m1_hits(_parts21)
assert collisions({"a.py": "_x = 1\n", "b.py": "def _x():\n    pass\n"}) == {"_x": ["a.py", "b.py"]}
assert collisions({"a.py": "_png = 1\n", "b.py": "_png = 2\n"}) == {}
assert not collisions(_parts21), collisions(_parts21)
print("OK OFFLINE 21t")


# %% OFFLINE 4d: open the run browser (shared by BROWSER 0 and BROWSER 2; takes `pw`, never imports it)
@dataclass(frozen=True)
class RunBrowser:
    context: object
    site_page: object
    control_page: object
    lock: CdpSiteLock
    surface: PlaywrightSurface
    control: BrowserControlWindow


async def open_run_browser(pw, user_dir: str, start_url: str,
                           cfg: DiscoveryConfig = CFG) -> RunBrowser:
    """Headed Chromium in app mode (no address bar). A PERSISTENT context is used because Playwright's
    plain launch() adds --no-startup-window, which makes --app a no-op; launch_persistent_context
    opens the --app window as the first page. `user_dir` should be a fresh temp dir per run."""
    w, h = cfg.viewport
    context = await pw.chromium.launch_persistent_context(
        user_dir, headless=False, args=["--app=about:blank"],
        viewport={"width": w, "height": h}, device_scale_factor=cfg.scale)
    site_page = context.pages[0] if context.pages else await context.new_page()
    lock = CdpSiteLock(await context.new_cdp_session(site_page))
    await lock.lock()  # locked BEFORE the site ever loads (Q-A: whole run)
    surface = PlaywrightSurface(site_page, lock)
    await surface.goto(start_url)  # host gate: an off-list start URL raises PermissionError
    control_page = await context.new_page()
    control = BrowserControlWindowTO(control_page)  # Q21: adds the Take over / Done pane
    await control.setup()
    return RunBrowser(context, site_page, control_page, lock, surface, control)


class _FakeCtxPage:
    """TEST ONLY."""
    def __init__(self, log: list, name: str) -> None:
        self.log, self.name, self.url = log, name, "about:blank"

    async def goto(self, url: str) -> None:
        self.log.append(("goto", self.name, url))
        self.url = url

    async def expose_function(self, name: str, callback) -> None:
        self.log.append(("expose_function", self.name, name))

    def on(self, event: str, handler) -> None:
        pass

    async def set_content(self, html: str) -> None:
        self.log.append(("set_content", self.name, len(html)))


class _FakeContext:
    """TEST ONLY."""
    def __init__(self, log: list) -> None:
        self.log = log
        self.pages = [_FakeCtxPage(log, "site")]
        self.cdp = FakeCdp()

    async def new_page(self) -> _FakeCtxPage:
        page = _FakeCtxPage(self.log, "control")
        self.pages.append(page)
        return page

    async def new_cdp_session(self, page: _FakeCtxPage) -> FakeCdp:
        self.log.append(("cdp", page.name))
        return self.cdp


class _FakeChromium:
    """TEST ONLY."""
    def __init__(self) -> None:
        self.log: list = []
        self.kwargs: dict = {}

    async def launch_persistent_context(self, user_dir: str, **kwargs) -> _FakeContext:
        self.kwargs = {"user_dir": user_dir, **kwargs}
        return _FakeContext(self.log)


class _FakePw:
    def __init__(self) -> None:
        self.chromium = _FakeChromium()


async def _test_open() -> None:
    pw = _FakePw()
    start = BASE + "/index.htm"  # the site value lives in the caller, never in the helper
    rb = await open_run_browser(pw, "/tmp/x", start)
    kw = pw.chromium.kwargs
    assert kw["headless"] is False and kw["viewport"] == {"width": 1280, "height": 800}
    assert kw["device_scale_factor"] == 1 and "--app=about:blank" in kw["args"]
    assert rb.site_page.name == "site" and rb.control_page.name == "control"
    assert ("goto", "site", start) in pw.chromium.log
    assert ("cdp", "site") in pw.chromium.log and ("cdp", "control") not in pw.chromium.log
    assert rb.lock.locked and rb.context.cdp.calls[-1] == ("Input.setIgnoreInputEvents", {"ignore": True})
    assert ("expose_function", "control", "cuaReply") in pw.chromium.log
    assert not [e for e in pw.chromium.log if e[0] in ("expose_function", "set_content") and e[1] == "site"]
    assert isinstance(rb.surface, PlaywrightSurface) and isinstance(rb.control, BrowserControlWindow)
    try:
        await open_run_browser(_FakePw(), "/tmp/y", "https://evil.com/")
        raise AssertionError("a start URL off the allow list must be refused")
    except PermissionError:
        pass


run_sync(_test_open())
print("OK OFFLINE 4d")


# %% OFFLINE 4e: lock-check helpers (find an input box between two labels, purely from OCR)
def field_between(found: list[tuple[str, Box, float]], top: str, bottom: str) -> Point | None:
    """Point of the empty input that sits under label `top` and above label `bottom`
    (a stacked login form). None when either label is missing or they are not stacked."""
    def first(word: str) -> Box | None:
        return next((b for t, b, _ in found if t.strip().casefold() == word.casefold()), None)
    a, b = first(top), first(bottom)
    if a is None or b is None or b.y1 <= a.y2:
        return None
    return Point(a.center.x, (a.y2 + b.y1) // 2)


def ocr_contains(found: list[tuple[str, Box, float]], word: str) -> bool:
    return any(word.casefold() in t.casefold() for t, _, _ in found)


_f = items(("Username", 40, 300, 120, 316), ("Password", 40, 360, 118, 376), ("Log In", 60, 420, 110, 440))
assert field_between(_f, "Username", "Password") == Point(80, 338)
assert field_between(_f, "Password", "Username") is None
assert field_between(_f, "Username", "Nope") is None
assert ocr_contains(_f, "log in") and not ocr_contains(_f, "probe")
print("OK OFFLINE 4e")


# %% [markdown]
# ## Live runs (OFFLINE 23 helpers, BROWSER 5-8)
# The BROWSER cells below are thin wiring: every piece of logic lives in OFFLINE 23 and is tested
# with fakes in OFFLINE 23t. Each run gets its own `runs/<run_id>/` folder, a fresh `AgentState`
# and a fresh agent, in the one browser opened by BROWSER 2 (site locked the whole time).


# %% OFFLINE 23: run helpers (new run dir, agent state, goal text, streaming, summary, audit)
import collections
import contextlib
import uuid

from cua.recorder import value_matches_type


def new_run(cfg: DiscoveryConfig, start_url: str, sitemap_urls: list[str],
            root: pathlib.Path = RUNS) -> tuple[str, pathlib.Path, EventLog]:
    """A fresh runs/<run_id>/ folder: run.json (M3) written first, then an empty event log."""
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    run_dir = root / run_id
    write_run_json(run_dir, cfg, start_url, run_id, len(sitemap_urls))
    return run_id, run_dir, EventLog(run_dir)


class AuditedControl:
    """Wraps the control window: every Approve / Reject is also written to the run's log as
    APPROVED / DECLINED, with whether the site was locked while the human decided (Q-A proof).
    Every other call (ask_value, status, ...) passes straight through."""

    def __init__(self, inner: ControlWindow, log: EventLog, lock: SiteLock) -> None:
        self._inner, self._log, self._lock = inner, log, lock

    async def approve(self, title: str, details: str, crop_png: bytes | None) -> Decision:
        decision = await self._inner.approve(title, details, crop_png)
        word = "APPROVED" if decision == "approve" else "DECLINED"
        locked = bool(getattr(self._lock, "locked", False))
        self._log.record("human_approval", {"title": title}, f"{word}: {title}",
                         EventExtras(extra={"site_locked": locked}))
        return decision

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def origin_secrets(url: str, resolve: Callable[[str], str] = resolve_secret) -> dict[str, str]:
    """Secret NAME -> value, only when `url` is a real page on an allowed host (never about:blank)."""
    if url == "about:blank" or not host_allowed(url):
        return {}
    return {name: resolve(name) for name in SECRETS}


def make_state(run: RunBrowser, log: EventLog, goal: str, cfg: DiscoveryConfig, ocr: OcrEngine,
               resolve: Callable[[str], str] = resolve_secret) -> AgentState:
    """One run's AgentState over the shared browser. Secrets are looked up by NAME for the current
    origin only; the control window is wrapped so approvals land in this run's log."""
    return AgentState(surface=run.surface, ocr=ocr, cfg=cfg, log=log, lock=run.lock,
                      control=AuditedControl(run.control, log, run.lock), given_text=goal,
                      secrets=origin_secrets(run.surface.url, resolve))


@dataclass(frozen=True)
class RunSetup:
    """What every live run in this session shares (keeps start_run within 6 parameters)."""
    cfg: DiscoveryConfig
    ocr: OcrEngine
    sitemap_urls: list[str]
    make_agent: Callable[[AgentState], object]   # BROWSER 5's build_langchain_agent wiring
    root: pathlib.Path = RUNS


@dataclass(frozen=True)
class LiveRun:
    run_id: str
    run_dir: pathlib.Path
    state: AgentState
    agent: object
    thread_id: str


def start_run(run: RunBrowser, goal: str, setup: RunSetup, session_dirs: list[pathlib.Path],
              resolve: Callable[[str], str] = resolve_secret) -> LiveRun:
    """New run dir + fresh AgentState + fresh agent (so no memory leaks between runs)."""
    run_id, run_dir, log = new_run(setup.cfg, run.surface.url, setup.sitemap_urls, setup.root)
    st = make_state(run, log, goal, setup.cfg, setup.ocr, resolve)
    session_dirs.append(run_dir)
    return LiveRun(run_id, run_dir, st, setup.make_agent(st), f"visual-{run_id}")


def require_filled(**values: str) -> None:
    """Refuse to start a run while a ground-truth value is still its <PLACEHOLDER> or empty."""
    bad = [k for k, v in values.items() if not v.strip() or (v.startswith("<") and v.endswith(">"))]
    if bad:
        raise ValueError(f"fill in these values at the top of the cell first: {', '.join(bad)}")


def goal_message(goal: str, sitemap_context: str) -> str:
    """The user message: the goal, plus the sitemap page list when one was found."""
    return f"{goal}\n\n{sitemap_context}" if sitemap_context else goal


def _text_of(content: object) -> str:
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content if isinstance(content, str) else ""


def _messages(chunk: object) -> list[tuple[str, object]]:
    """(node, message) pairs from one LangGraph `updates` chunk; odd shapes are skipped."""
    pairs: list[tuple[str, object]] = []
    for node, update in (chunk.items() if isinstance(chunk, dict) else ()):
        msgs = update.get("messages") if isinstance(update, dict) else None
        if isinstance(msgs, list):
            pairs.extend((node, m) for m in msgs)
    return pairs


async def stream_agent(agent: object, message: str, thread_id: str, max_steps: int,
                       out: Callable[[str], None] = print) -> str:
    """Stream one run; print each tool call and the first line of its result. Returns the agent's
    last text, or "STUCK: ..." once more than `max_steps` tool calls were made (the step cap)."""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10 * max_steps + 20}
    payload = {"messages": [{"role": "user", "content": message}]}
    steps, final = 0, ""
    stream = agent.astream(payload, config=config, stream_mode="updates")
    async with contextlib.aclosing(stream):
        async for chunk in stream:
            for node, m in _messages(chunk):
                calls = getattr(m, "tool_calls", None) or []
                for call in calls:
                    steps += 1
                    out(f"{steps:3d} -> {call.get('name')}({json.dumps(call.get('args'), default=str)})")
                if steps > max_steps:
                    return f"STUCK: step cap of {max_steps} tool calls reached."
                if node == "tools" or getattr(m, "type", "") == "tool":
                    first = _text_of(m.content).strip().splitlines()[:1]
                    out(f"      <- {getattr(m, 'name', '')}: {(first or [''])[0][:140]}")
                elif not calls:
                    final = _text_of(m.content) or final
    return final


def read_events(run_dir: pathlib.Path) -> list[dict]:
    path = run_dir / "events.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run_summary(run_dir: pathlib.Path) -> dict[str, object]:
    """Counts for one run: steps, tools used, human entries, takeovers, hints, crops, approvals."""
    ev = read_events(run_dir)
    secret = [e for e in ev if e["tool"] == "type_secret" and e["crop"]]
    approvals = [e for e in ev if e["tool"] == "human_approval"]
    return {
        "steps": len(ev),
        "tools": dict(collections.Counter(e["tool"] for e in ev)),
        "human_entry": sum(1 for e in ev if e["human_entry"]),
        "takeovers": sum(1 for e in ev if "take_over" in e["tool"] or (e["extra"] or {}).get("take_over")),
        "hints": sum(1 for e in ev if e["hints"]),
        "table_reads": sum(1 for e in ev if e["hints"] and e["hints"].get("table")),
        "crops": sum(1 for e in ev if e["crop"]),
        "approved": sum(1 for e in approvals if e["result"].startswith("APPROVED")),
        "declined": sum(1 for e in ev if e["result"].startswith("DECLINED")),
        "approval_results": [e["result"] for e in approvals],
        "approvals_locked": bool(approvals) and all((e["extra"] or {}).get("site_locked") for e in approvals),
        "secret_crops": len(secret),
        "secret_crop_paths": [e["crop"] for e in secret],
        "saved": {e["args"]["save_as"]: e["args"]["value_type"] for e in ev
                  if e["tool"] == "extract_value" and e["result"].startswith("OK")},
    }


def _audit_run_json(run_dir: pathlib.Path) -> list[str]:
    try:
        data = json.loads((run_dir / "run.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"run.json missing or not valid JSON ({type(exc).__name__})"]
    need = {"version", "run_id", "start_url", "viewport", "device_scale_factor", "zoom"}
    if not need <= set(data) or data["version"] != RUN_JSON_VERSION:
        return ["run.json does not match the version-1 format"]
    return [] if host_allowed(data["start_url"]) else ["run.json start_url is off the allowed host"]


def audit_run(run_dir: pathlib.Path, secret_values: list[str]) -> list[str]:
    """Problems with one run dir ([] = clean). A problem text names the secret by position and the
    file, never the value. Checks: no secret in any file, run.json valid, every picture exists."""
    problems = _audit_run_json(run_dir)
    for i, value in enumerate(v for v in secret_values if v):
        try:
            assert_no_secret(run_dir, value)
        except AssertionError as exc:
            problems.append(f"secret #{i + 1}: {exc}")
    for e in read_events(run_dir):
        paths = [e["shot"], e["crop"], (e["hints"] or {}).get("crop_path")]
        problems += [f"step {e['step']}: missing file {p}" for p in paths if p and not (run_dir / p).is_file()]
    return problems


def read_run_checks(summary: dict, run_dir: pathlib.Path, saved_values: dict[str, str]) -> dict[str, bool]:
    """Run 1 expectations (PLAN Task 7, BROWSER 6)."""
    saved = summary["saved"]
    return {
        "type_secret used": summary["tools"].get("type_secret", 0) >= 1,
        "currency balance saved": any(t == "currency" and value_matches_type(saved_values.get(n, ""), t)
                                      for n, t in saved.items()),
        "table read in hints": summary["table_reads"] >= 1,
        "password crop exists": any((run_dir / p).is_file() for p in summary["secret_crop_paths"]),
    }


def transfer_run_checks(summary: dict, expect: Decision, target: str,
                        site_locked_now: bool) -> dict[str, bool]:
    """Run 2 expectations (BROWSER 7): the human's decision on the `target` click is in the log
    (other approvals, e.g. Log In, don't count) and the site stayed locked throughout."""
    want = normalise(target)
    hits = [r for r in summary["approval_results"] if want in map(normalise, re.findall(r"'([^']*)'", r))]
    approved = any(r.startswith("APPROVED") for r in hits)
    got = ({f"{target!r} APPROVED in the log": approved} if expect == "approve" else
           {f"{target!r} DECLINED in the log": any(r.startswith("DECLINED") for r in hits),
            f"{target!r} never APPROVED": not approved})
    return {**got, "site locked at every approval": summary["approvals_locked"],
            "site locked now": site_locked_now}


print("OK OFFLINE 23")


# %% OFFLINE 23t: tests for the run helpers (temp run dirs, a FAKE secret, no browser, no model)
import tempfile as _tf23
from types import SimpleNamespace as _NS23

_FAKE_SECRET23 = "hunter2-fake-secret"
_URL23 = BASE + "/index.htm"


def _fake_run23(url: str = _URL23) -> _NS23:
    return _NS23(surface=FakeSurface([(b"png", [])], url), lock=_NS23(locked=True),
                 control=FakeControl(["approve", "reject"]))


def _test_23_new_run(root: pathlib.Path) -> None:
    rid, rdir, log = new_run(CFG, _URL23, ["a", "b"], root=root)
    assert rdir == root / rid and isinstance(log, EventLog) and log.run_dir == rdir
    data = json.loads((rdir / "run.json").read_text())
    assert data["run_id"] == rid and data["sitemap_pages"] == 2 and data["start_url"] == _URL23
    rid2, _, _ = new_run(CFG, _URL23, [], root=root)
    assert rid2 != rid, "every run gets its own id"


def _test_23_make_state(root: pathlib.Path) -> None:
    asked: list[str] = []
    fake_resolve = lambda name: asked.append(name) or _FAKE_SECRET23  # noqa: E731
    _, _, log = new_run(CFG, _URL23, [], root=root)
    st = make_state(_fake_run23(), log, "read a balance", CFG, lambda png: [], resolve=fake_resolve)
    assert isinstance(st, AgentState) and st.given_text == "read a balance" and st.log is log
    assert set(st.secrets) == set(SECRETS) and sorted(asked) == sorted(SECRETS), "looked up by NAME"
    off = make_state(_fake_run23("https://evil.com/x"), log, "g", CFG, lambda png: [], resolve=fake_resolve)
    assert off.secrets == {}, "no secret for an origin off the allow list"
    blank = make_state(_fake_run23("about:blank"), log, "g", CFG, lambda png: [], resolve=fake_resolve)
    assert blank.secrets == {}, "about:blank is not a real origin"


async def _test_23_audited_control(root: pathlib.Path) -> None:
    _, rdir, log = new_run(CFG, _URL23, [], root=root)
    st = make_state(_fake_run23(), log, "g", CFG, lambda png: [], resolve=lambda n: "x-fake")
    assert await st.control.approve("Click 'Transfer'?", "d", b"crop") == "approve"
    assert await st.control.approve("Click 'Transfer'?", "d", None) == "reject"
    await st.control.status("hi")  # other methods pass straight through
    ev = [json.loads(line) for line in log.path.read_text().splitlines()]
    assert [e["result"].split(":")[0] for e in ev] == ["APPROVED", "DECLINED"]
    assert all(e["tool"] == "human_approval" and e["extra"]["site_locked"] is True for e in ev)
    assert st.control.statuses == ["hi"]
    open_run = _fake_run23()
    open_run.lock = _NS23(locked=False)
    st2 = make_state(open_run, log, "g", CFG, lambda png: [], resolve=lambda n: "x-fake")
    await st2.control.approve("t", "d", None)
    assert run_summary(rdir)["approvals_locked"] is False, "an unlocked approval must show up"


def _test_23_goal_message() -> None:
    assert goal_message("Read it.", "") == "Read it."
    msg = goal_message("Read it.", "Pages listed:\n/a.htm")
    assert msg.startswith("Read it.") and msg.endswith("/a.htm") and "\n\n" in msg


def _write_events23(rdir: pathlib.Path, secret_in_log: bool) -> None:
    log = EventLog(rdir)
    log.record("observe", {}, "Screen gen 1", EventExtras(shot_png=b"\x89PNG-shot"))
    log.record("type_secret", {"secret_name": "password"}, "OK: typed",
               EventExtras(crop_png=b"\x89PNG-pw", hints=RungHints(None, Anchor("Password", 0, 150, 0), None, None)))
    table = RungHints("$100.00", None, None, TableRead("13344", "Balance"))
    log.record("extract_value", {"save_as": "balance", "value_type": "currency"}, "OK: saved 'balance' (currency).",
               EventExtras(crop_png=b"\x89PNG-bal", hints=table))
    log.record("type_text", {"field": "Phone"}, "OK", EventExtras(human_entry=True))
    log.record("human_approval", {"title": "t"}, "DECLINED: t", EventExtras(extra={"site_locked": True}))
    if secret_in_log:
        log.record("finish", {"summary": _FAKE_SECRET23}, "FINISHED:")


def _test_23_summary(root: pathlib.Path) -> None:
    _, rdir, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(rdir, secret_in_log=False)
    s = run_summary(rdir)
    assert s["steps"] == 5 and s["tools"]["type_secret"] == 1 and s["human_entry"] == 1
    assert s["takeovers"] == 0 and s["hints"] == 2 and s["table_reads"] == 1 and s["crops"] == 2
    assert s["approved"] == 0 and s["declined"] == 1 and s["secret_crops"] == 1
    assert s["saved"] == {"balance": "currency"}


def _test_23_audit(root: pathlib.Path) -> None:
    _, good, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(good, secret_in_log=False)
    assert audit_run(good, [_FAKE_SECRET23]) == []
    _, bad, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(bad, secret_in_log=True)
    (bad / "crops" / "003.png").unlink()
    problems = audit_run(bad, [_FAKE_SECRET23, ""])
    assert any("secret" in p for p in problems) and any("003.png" in p for p in problems), problems
    assert not any(_FAKE_SECRET23 in p for p in problems), "a problem message never carries the value"
    (bad / "run.json").write_text("{not json")
    assert any("run.json" in p for p in audit_run(bad, [])), "a broken run.json is reported"


def _test_23_checks(root: pathlib.Path) -> None:
    _, rdir, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(rdir, secret_in_log=False)
    s = run_summary(rdir)
    ok = read_run_checks(s, rdir, {"balance": "$100.00"})
    assert ok == {"type_secret used": True, "currency balance saved": True,
                  "table read in hints": True, "password crop exists": True}, ok
    assert not read_run_checks(s, rdir, {"balance": "n/a"})["currency balance saved"]
    log = EventLog(rdir)
    for t in ("Click 'Log In'?", "Click 'Transfer Funds'?"):
        log.record("human_approval", {"title": t}, f"APPROVED: {t}", EventExtras(extra={"site_locked": True}))
    log.record("human_approval", {"title": "Click 'Transfer'?"}, "DECLINED: Click 'Transfer'?",
               EventExtras(extra={"site_locked": True}))
    s = run_summary(rdir)
    assert transfer_run_checks(s, "reject", "Transfer", site_locked_now=True) == {
        "'Transfer' DECLINED in the log": True, "'Transfer' never APPROVED": True,
        "site locked at every approval": True, "site locked now": True}
    assert not all(transfer_run_checks(s, "approve", "Transfer", site_locked_now=True).values()), \
        "an approved 'Log In' must not count as an approved transfer"
    assert not transfer_run_checks(s, "reject", "Transfer", site_locked_now=False)["site locked now"]


def _test_23_start_run(root: pathlib.Path) -> None:
    built: list[AgentState] = []
    make_agent = lambda st: built.append(st) or "agent-for-" + st.given_text  # noqa: E731
    session: list[pathlib.Path] = []
    lr = start_run(_fake_run23(), "move $5", RunSetup(CFG, lambda png: [], [], make_agent, root),
                   session, resolve=lambda n: "x-fake")
    assert lr.agent == "agent-for-move $5" and built == [lr.state] and session == [lr.run_dir]
    assert lr.state.log.run_dir == lr.run_dir and (lr.run_dir / "run.json").is_file()
    assert lr.thread_id.startswith("visual-") and lr.run_id in lr.thread_id


def _test_23_require_filled() -> None:
    require_filled(ACCOUNT_ID="13344", AMOUNT="5.00")
    for bad in ("<YOUR ACCOUNT ID>", "", "  "):
        with contextlib.suppress(ValueError):
            require_filled(ACCOUNT_ID=bad)
            raise AssertionError(f"placeholder {bad!r} must be refused")


class _FakeAgent23:
    """TEST ONLY: yields LangGraph-style `updates` chunks (one AI tool call, then its result)."""

    def __init__(self, turns: int) -> None:
        self.turns, self.config = turns, None

    async def astream(self, payload: dict, config: dict, stream_mode: str):
        self.config = config
        for i in range(self.turns):
            call = _NS23(content="", tool_calls=[{"name": "observe", "args": {"i": i}}])
            yield {"model": {"messages": [call]}}
            yield {"tools": {"messages": [_NS23(name="observe", content=f"Screen gen {i}\n[1] 'x'", tool_calls=[])]}}
        yield {"model": {"messages": [_NS23(content=[{"type": "text", "text": "All done."}], tool_calls=[])]}}


async def _test_23_stream() -> None:
    lines: list[str] = []
    fa = _FakeAgent23(2)
    final = await stream_agent(fa, "go", "t-1", 10, out=lines.append)
    assert final == "All done." and fa.config["configurable"]["thread_id"] == "t-1"
    assert fa.config["recursion_limit"] > 10
    assert sum("observe" in ln and "->" in ln for ln in lines) == 2
    assert any("Screen gen 0" in ln and "[1]" not in ln for ln in lines), "result prefix = first line only"
    capped = await stream_agent(_FakeAgent23(5), "go", "t-2", 3, out=lines.append)
    assert capped.startswith("STUCK:"), capped


with _tf23.TemporaryDirectory() as _d23:
    _root23 = pathlib.Path(_d23)
    _test_23_new_run(_root23)
    _test_23_make_state(_root23)
    run_sync(_test_23_audited_control(_root23))
    _test_23_goal_message()
    _test_23_summary(_root23)
    _test_23_audit(_root23)
    _test_23_checks(_root23)
    _test_23_start_run(_root23)
_test_23_require_filled()
run_sync(_test_23_stream())
print("OK OFFLINE 23t")


# %% BROWSER 0: THE LOCK CHECK (run first; the whole Q-A design depends on it)
# Opens its own throwaway browser, runs (a)-(d), prints PASS/FAIL, closes everything.
# App mode: a persistent context is needed for --app to take effect (see open_run_browser).
import tempfile

from playwright.async_api import async_playwright


async def _lock_ocr(page) -> list[tuple[str, Box, float]]:
    png = await page.screenshot(type="png")
    return await asyncio.to_thread(_LOCK_OCR, png)


async def _lock_step_a(rb: RunBrowser) -> bool:
    before = await rb.surface.screenshot()
    print("\n(a) The site window is LOCKED. For the next 10 seconds, try to click the Username box and")
    print("    type something, click links, scroll. Also look: is there an address bar? (there should be none)")
    await asyncio.sleep(10)
    after = await rb.surface.screenshot()
    same = screens_same(before, after, CFG)
    print(f"    screen unchanged after your 10 s: {same}")
    print("    Did your clicks or typing do anything? (look at the window)")
    return same


async def _lock_step_b(rb: RunBrowser, field: Point) -> bool:
    print("\n(b) While LOCKED, Playwright itself clicks the Username box and types 'probe' (no unlock).")
    await rb.site_page.mouse.click(field.x, field.y)
    await rb.site_page.keyboard.type("probe")
    blocked = not ocr_contains(await _lock_ocr(rb.site_page), "probe")
    print(f"    our own input blocked by the lock: {blocked} (info only: during() must unlock for us)")
    return blocked


async def _lock_step_c(rb: RunBrowser, field: Point) -> bool:
    print("\n(c) unlock -> click + type 'lockok' -> relock, via SITE_LOCK.during() (PlaywrightSurface).")
    await rb.surface.click(field.x, field.y)
    await rb.surface.type("lockok")
    typed = ocr_contains(await _lock_ocr(rb.site_page), "lockok")
    print(f"    'lockok' visible by OCR: {typed}; lock re-engaged: {rb.lock.locked}")
    return typed and rb.lock.locked


async def _lock_step_d(rb: RunBrowser) -> bool:
    print("\n(d) Go to the CONTROL window (the second window) and click Approve.")
    await rb.control.status("Lock check: step (d)")
    decision = await asyncio.wait_for(rb.control.approve(
        "Lock check (d): click Approve", "The site stays locked; this window must still work.", None), 120)
    print(f"    control window answered: {decision}; site still locked: {rb.lock.locked}")
    return decision == "approve" and rb.lock.locked


async def run_lock_check() -> dict[str, bool]:
    pw = await async_playwright().start()
    rb = None
    try:
        rb = await open_run_browser(pw, tempfile.mkdtemp(prefix="cua-lockcheck-"), START_URL)
        field = field_between(await _lock_ocr(rb.site_page), "Username", "Password")
        if field is None:
            raise RuntimeError("could not find the Username box by OCR; the lock check cannot run")
        return {"a_human_blocked": await _lock_step_a(rb),
                "b_our_input_blocked_while_locked (info)": await _lock_step_b(rb, field),
                "c_unlock_act_relock": await _lock_step_c(rb, field),
                "d_control_window_usable": await _lock_step_d(rb)}
    finally:
        if rb is not None:
            await rb.context.close()
        await pw.stop()


START_URL = BASE + "/index.htm"  # site value: config (BASE) + this run cell only
_LOCK_OCR = make_ocr_engine()
LOCK_RESULT = await run_lock_check()
print("\n==== LOCK CHECK ====")
for _k, _v in LOCK_RESULT.items():
    print(f"  {_k}: {_v}")
_lock_pass = all(v for k, v in LOCK_RESULT.items() if "(info)" not in k)
if _lock_pass:
    print("PASS: the lock blocks the human, lets our own action through, and the control window works.")
    print("      Also confirm by eye: in (a) nothing you did had any effect, and there was no address bar.")
else:
    print("FAIL")
    print("STOP: re-decide Q-A before continuing")


# %% BROWSER 2: the real browser for the run (site locked from the first moment, Q-A)
import tempfile

from playwright.async_api import async_playwright

pw = await async_playwright().start()
START_URL = BASE + "/index.htm"  # site value: config (BASE) + this run cell only
RUN = await open_run_browser(pw, tempfile.mkdtemp(prefix="cua-run-"), START_URL)
context, site_page, control_page = RUN.context, RUN.site_page, RUN.control_page
SITE_LOCK, SURFACE, CONTROL = RUN.lock, RUN.surface, RUN.control
assert SITE_LOCK.locked, "the site must be locked for the whole run"
await CONTROL.status("Browser ready. Site is locked.")

_first = await SURFACE.screenshot()
_shape = png_to_bgr(_first).shape
assert _shape[:2] == (CFG.viewport[1], CFG.viewport[0]), f"screenshot is {_shape[1]}x{_shape[0]}, not 1280x800"
print(f"OK BROWSER 2: {SURFACE.url} | screenshot {_shape[1]}x{_shape[0]} | site locked: {SITE_LOCK.locked}")


# %% BROWSER 2b: SITEMAP. Runs once, before discovery. Not found -> carry on as usual.
# The user's own two usp lines, which fetch_sitemap_urls (OFFLINE 2b) wraps with the host gate:
#     tree = sitemap_tree_for_homepage(SITE)
#     for page in tree.all_pages(): ...page.url
# Expected on ParaBank today (no /sitemap.xml): "sitemap: none found, continuing as usual".
SITE = BASE                                   # the website we are discovering (from config)
SITEMAP_URLS = await asyncio.to_thread(fetch_sitemap_urls, SITE)
SITEMAP_CONTEXT = sitemap_context(SITEMAP_URLS, globals().get("RUN_CFG", CFG))
print(f"sitemap: {len(SITEMAP_URLS)} pages found" if SITEMAP_URLS else "sitemap: none found, continuing as usual")


# %% BROWSER 3: first look at the ParaBank login screen (OCR -> numbers -> picture)
from IPython.display import Image, display

_ocr = make_ocr_engine()
_png = await SURFACE.screenshot()
_found = await asyncio.to_thread(_ocr, _png)
_els = number(_found, RefCounter())  # display-only look; the agent keeps its own run-wide counter
display(Image(draw_numbered(_png, _els)))
print(format_elements(_els))

(FIXTURES / "png").mkdir(parents=True, exist_ok=True)
(FIXTURES / "png" / "parabank_login.png").write_bytes(_png)  # raw (no boxes), for OCR regression
_texts = {e.text.strip().casefold() for e in _els}
for _w in ("username", "password", "log in"):
    print(f"  {_w!r} numbered: {_w in _texts}")
print("Check by eye: Username / Password / Log In have numbers; the two EMPTY boxes do not.")


# %% BROWSER 5: build the agent (needs BROWSER 2 + 2b; p3b's build_tools / VISUAL_SYSTEM_PROMPT / build_middleware)
import tempfile

from IPython.display import Image, display

from cua.models import make_chat_model, model_name_for

RUN_MODEL = model_name_for("sonnet")                         # Iliad gateway Sonnet (ILIAD_SONNET_MODEL)
MAX_STEPS = 40                                               # step cap per run (tool calls)
# Q-B: ParaBank's safe list lives HERE (the run cell), never in tool code. (page, OCR text) pairs.
_MENU = ("Accounts Overview", "Transfer Funds", "Find Transactions", "Log Out")
RUN_CFG = dataclasses.replace(CFG, safe_clicks=frozenset(
    {("index.htm", "Log In")} | {(p, t) for p in ("overview.htm", "transfer.htm", "activity.htm") for t in _MENU}))
RUN_OCR = make_ocr_engine()
SESSION_RUNS: list[pathlib.Path] = []                        # every run dir made this session (BROWSER 8)


def _make_agent(st: AgentState) -> object:
    return build_langchain_agent(build_tools(st), model=make_chat_model("sonnet"), system_prompt=VISUAL_SYSTEM_PROMPT,
                                 middleware=build_middleware(st))


SETUP = RunSetup(RUN_CFG, RUN_OCR, SITEMAP_URLS, _make_agent)
# A dry build (log in a throwaway dir outside runs/), only to show what the model gets.
st = make_state(RUN, EventLog(pathlib.Path(tempfile.mkdtemp(prefix="cua-dry-"))), "", RUN_CFG, RUN_OCR)
agent = _make_agent(st)
print(f"model: {RUN_MODEL} | step cap: {MAX_STEPS} | secret names: {sorted(st.secrets)}")
print("tools:", ", ".join(t.name for t in build_tools(st)))
print(f"OK BROWSER 5 (site locked: {SITE_LOCK.locked})")


# %% BROWSER 6: run 1, read a balance (log in by type_secret, table read, extract_value, log out)
ACCOUNT_ID = "<YOUR ACCOUNT ID>"   # ground truth: EDIT ME, one of your own fake ParaBank account ids
require_filled(ACCOUNT_ID=ACCOUNT_ID)

GOAL1 = (f"Log in with type_secret, read the balance of account {ACCOUNT_ID}, "
         "save it with extract_value, then log out.")
print("You: watch the control window. Approve clicks that match the goal; the site stays locked.")
await SURFACE.goto(BASE + "/index.htm")
RUN1 = start_run(RUN, GOAL1, SETUP, SESSION_RUNS)
print(f"run 1: {RUN1.run_dir}")
FINAL1 = await stream_agent(RUN1.agent, goal_message(GOAL1, SITEMAP_CONTEXT), RUN1.thread_id, MAX_STEPS)
print("\nAGENT SAID:", FINAL1)
SUMMARY1 = run_summary(RUN1.run_dir)
print(json.dumps({k: v for k, v in SUMMARY1.items() if k != "approval_results"}, indent=2))
print("saved values:", RUN1.state.saved)
for _k, _v in read_run_checks(SUMMARY1, RUN1.run_dir, RUN1.state.saved).items():
    print(f"  {'PASS' if _v else 'FAIL'}  {_k}")
print("Eye check: the password-box crop(s) below must show an EMPTY box (cut before typing).")
for _p in SUMMARY1["secret_crop_paths"]:
    display(Image((RUN1.run_dir / _p).read_bytes()))


# %% BROWSER 7: run 2, a small transfer between your own two accounts (run twice: Approve, then Reject)
FROM_ACCOUNT = "<FROM ACCOUNT ID>"   # ground truth: EDIT ME, your own fake account to send from
TO_ACCOUNT = "<TO ACCOUNT ID>"       # ground truth: EDIT ME, your own OTHER fake account
AMOUNT = "<AMOUNT, e.g. 5.00>"       # ground truth: EDIT ME, keep it small
TRANSFER_BUTTON = "Transfer"         # the risky submit button's text, as the control window shows it
require_filled(FROM_ACCOUNT=FROM_ACCOUNT, TO_ACCOUNT=TO_ACCOUNT, AMOUNT=AMOUNT)

GOAL2 = (f"Log in with type_secret, open Transfer Funds, and transfer ${AMOUNT} from account "
         f"{FROM_ACCOUNT} to account {TO_ACCOUNT}. If the transfer is declined, finish with DECLINED:. "
         "Then log out.")
RUNS2: dict[str, LiveRun] = {}
for _decision in ("approve", "reject"):
    _word = "APPROVE" if _decision == "approve" else "REJECT"
    print(f"\n==== run 2 ({_decision}) ====")
    print(f"You: Approve the ordinary steps in the control window. When it asks to click "
          f"{TRANSFER_BUTTON!r}, click {_word}. Never touch the site window.")
    await SURFACE.goto(BASE + "/index.htm")
    _lr = start_run(RUN, GOAL2, SETUP, SESSION_RUNS)
    RUNS2[_decision] = _lr
    _final = await stream_agent(_lr.agent, goal_message(GOAL2, SITEMAP_CONTEXT), _lr.thread_id, MAX_STEPS)
    print("AGENT SAID:", _final)
    _s = run_summary(_lr.run_dir)
    print("approvals:", _s["approval_results"])
    for _k, _v in transfer_run_checks(_s, _decision, TRANSFER_BUTTON, SITE_LOCK.locked).items():
        print(f"  {'PASS' if _v else 'FAIL'}  {_k}")


# %% BROWSER 8: audit every run dir from this session, show every crop, close the browser
_secret_values = list(origin_secrets(BASE + "/index.htm").values())   # kept local; never printed
for _dir in SESSION_RUNS:
    _problems = audit_run(_dir, _secret_values)
    print(f"{_dir.name}: {'CLEAN' if not _problems else 'PROBLEMS'}")
    for _p in _problems:
        print("   -", _p)
del _secret_values
print("\nEye check: no customer data (names, addresses, other accounts) may be visible in any crop.")
for _dir in SESSION_RUNS:
    for _crop in sorted((_dir / "crops").glob("*.png")):
        print(f"{_dir.name}/crops/{_crop.name}")
        display(Image(_crop.read_bytes()))
await CONTROL.status("Run finished. Closing.")
await context.close()
await pw.stop()
print("OK BROWSER 8: browser closed")

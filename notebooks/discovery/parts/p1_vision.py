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

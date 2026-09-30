# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: interface-ai-cua (3.12.2)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Visual replay
# Runs a capability saved by discovery with plain code, no LLM. Every send meets both human gates.

# %% [markdown]
# ## Setup
# Imports and `.env`. No model: replay only follows the saved steps.

# %%
import ast
import asyncio
import base64
import contextlib
import difflib
import functools
import html
import json
import math
import os
import re
import tempfile
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

import cv2
import numpy as np
import yaml
from dotenv import load_dotenv
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from pydantic import ValidationError
from rapidocr import RapidOCR


load_dotenv(override=True)

# %% [markdown]
# ## Config & secrets
# Site values and thresholds. Secrets come from `.env`; only their names are ever shown.

# %%
ALLOWED_HOSTS = {"parabank.parasoft.com"}
SECRET_ENV = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}
SECRETS = {name: os.getenv(env, "") for name, env in SECRET_ENV.items()}


def host_allowed(url: str) -> bool:
    return url == "about:blank" or urlparse(url).hostname in ALLOWED_HOSTS


@dataclass(frozen=True)
class Config:
    viewport: tuple[int, int] = (1280, 800)       # Q10: same as discovery; refuse otherwise
    ocr_min_score: float = 0.5
    scroll_px: int = 600
    same_screen_mad: float = 1.0
    crop_pad: int = 6
    point_crop: tuple[int, int] = (160, 34)
    settle_ms: int = 600
    sensitive_words: frozenset[str] = frozenset({"password", "ssn", "social"})
    login_words: frozenset[str] = frozenset({"log in"})
    fuzzy: float = 0.8                # rung 1/2 text similarity (words only; digits match exactly)
    template_threshold: float = 0.8   # rung 3 matchTemplate score
    template_margin: float = 0.05     # a second peak this close to the best = ambiguous = miss
    scroll_retries: int = 1           # all rungs miss -> scroll down, retry this many times
    check_s: float = 5.0              # OCR poll budget for an `expect` check
    poll_ms: int = 200
    snap_s: float = 3.0               # evidence screenshot budget; a held send can block screenshots
    page_s: float = 2.0               # any other page read near a send (evaluate can block too)
    gate_s: float = 120.0             # hand-back waits this long for a send still at the gates
    field_min: tuple[int, int] = (40, 16)   # smallest drawn box that counts as an input field
    short_value: int = 2              # a typed value this short is checked by pixels if OCR misses it
    near_px: float = 60.0             # rung 1 with duplicate text: a copy this close to the anchor's point
    ext_s: float = 1.0                # any one call into the hand-back extension gives up after this
    ext_poll_s: float = 0.5           # take-over: how often the toolbar button's clicks are read
    # R17 taxonomy: text seen after a step -> status. First match wins; a capability's own
    # `outcomes:` list replaces these. RECOVER = log in again once and retry the step.
    outcomes: tuple[dict, ...] = (
        {"text": "not found", "status": "BUSINESS_OUTCOME", "meaning": "the item asked for was not found"},
        {"text": "no such", "status": "BUSINESS_OUTCOME", "meaning": "the item asked for does not exist"},
        {"text": "does not exist", "status": "BUSINESS_OUTCOME", "meaning": "the item does not exist"},
        {"text": "insufficient funds", "status": "BUSINESS_OUTCOME", "meaning": "not enough funds"},
        {"text": "could not be verified", "status": "BUSINESS_OUTCOME", "meaning": "details not verified"},
        {"text": "session expired", "status": "RECOVER", "meaning": "the session expired"},
        {"text": "access denied", "status": "FAILED", "meaning": "the site denied access"},
        {"text": "error", "status": "FAILED", "meaning": "the site showed an error page"},
    )


CFG = Config()
print("secrets set:", sorted(n for n, v in SECRETS.items() if v))

# %% [markdown]
# ## Browser
# One visible Chromium at the fixed page size, plus the "Agent control" tab. Same as discovery,
# including the hand-back extension (R19): a toolbar button, no content scripts, no host access.
# `EXT` is its service worker, or None if it did not load.

# %%
need_new_pages = any(n not in globals() or globals()[n].is_closed() for n in ("page", "control_page"))

if need_new_pages:
    if "pw" not in globals():
        pw = await async_playwright().start()
    w, h = CFG.viewport
    ext_dir = next(p / "extensions/handback" for p in (Path.cwd(), *Path.cwd().parents)
                   if (p / "extensions/handback/manifest.json").is_file())
    context = await pw.chromium.launch_persistent_context(
        tempfile.mkdtemp(prefix="cua-replay-"), headless=False, viewport={"width": w, "height": h},
        device_scale_factor=1, args=[f"--window-size={w},{h + 140}",
                                     f"--disable-extensions-except={ext_dir}", f"--load-extension={ext_dir}"])
    page = context.pages[0] if context.pages else await context.new_page()
    control_page = await context.new_page()
    try:
        EXT = context.service_workers[0] if context.service_workers else \
            await context.wait_for_event("serviceworker", timeout=5000)
    except PlaywrightError:
        EXT = None                    # the take-over still hands back from the control tab
    print("hand-back extension:", "loaded" if EXT else "NOT loaded")
print("browser open | page", CFG.viewport)

# %% [markdown]
# ## Vision (reused from discovery)
# Screenshot, RapidOCR, numbered boxes, and the pixel checks. Copied from discovery; `HANDOFF` is `STATE`.

# %%
@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def overlaps(self, o: "Box") -> bool:
        return self.x1 < o.x2 and o.x1 < self.x2 and self.y1 < o.y2 and o.y1 < self.y2


@dataclass(frozen=True)
class Element:
    ref: int
    text: str
    box: Box


@dataclass(frozen=True)
class Look:
    png: bytes
    drawn: bytes
    elements: tuple[Element, ...]
    url: str
    scale: float = 1.0

    def get(self, ref: int) -> Element | None:
        return next((e for e in self.elements if e.ref == ref), None)

    @property
    def text(self) -> str:
        return " ".join(e.text for e in self.elements)


OCR_ENGINE = RapidOCR()
REFS = {"next": 1}


def decode(png: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)


def encode(img: np.ndarray) -> bytes:
    return cv2.imencode(".png", img)[1].tobytes()


def ocr(img: np.ndarray) -> list[tuple[str, Box]]:
    out = OCR_ENGINE(img)
    if out.boxes is None:
        return []
    items = []
    for quad, txt, score in zip(out.boxes, out.txts, out.scores):
        if score >= CFG.ocr_min_score and txt.strip():
            xs, ys = [p[0] for p in quad], [p[1] for p in quad]
            items.append((txt.strip(), Box(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))))
    return items


def number(items: list[tuple[str, Box]]) -> tuple[Element, ...]:
    """Reading order (rows top to bottom, then left to right), fresh refs."""
    rows: list[list[tuple[str, Box]]] = []
    for it in sorted(items, key=lambda t: t[1].y1):
        first = rows[-1][0][1] if rows else None
        if first and it[1].y1 < first.y2 and it[1].y2 > first.y1:
            rows[-1].append(it)
        else:
            rows.append([it])
    out = []
    for text, box in (it for row in rows for it in sorted(row, key=lambda t: t[1].x1)):
        out.append(Element(REFS["next"], text, box))
        REFS["next"] += 1
    return tuple(out)


def draw_numbered(img: np.ndarray, elements: tuple[Element, ...]) -> bytes:
    out = img.copy()
    for e in elements:
        b = e.box
        cv2.rectangle(out, (b.x1, b.y1), (b.x2, b.y2), (0, 0, 255), 1)
        cv2.putText(out, str(e.ref), (b.x1, max(b.y1 - 3, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 0, 255), 1)
    return encode(out)


async def take_look() -> Look:
    img, points_w = decode(await page.screenshot()), await page_width()
    img, scale = to_canvas(img, points_w)
    elements = number(ocr(img))
    STATE.look = Look(encode(img), draw_numbered(img, elements), elements, page.url, scale)
    return STATE.look


def to_canvas(img: np.ndarray, points_w: int) -> tuple[np.ndarray, float]:
    cw, ch = CFG.viewport
    f = min(cw / img.shape[1], ch / img.shape[0])
    out = cv2.resize(img, (round(img.shape[1] * f), round(img.shape[0] * f)),
                     interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC)
    return out, points_w / out.shape[1]


async def page_width() -> int:
    return int(await page.evaluate("window.innerWidth"))


def canvas() -> tuple[int, int]:
    if STATE.look is None:
        return CFG.viewport
    h, w = decode(STATE.look.png).shape[:2]
    return w, h


def to_page(point: tuple[int, int]) -> tuple[float, float]:
    s = STATE.look.scale if STATE.look else 1.0
    return point[0] * s, point[1] * s


def hide_secrets(text: str) -> str:
    for name, value in SECRETS.items():
        if value:
            text = text.replace(value, f"<{name}>")
    return text


# %%
def element_at(look: Look, point: tuple[int, int]) -> Element | None:
    return next((e for e in look.elements if e.box.contains(*point)), None)


def crop_box(point: tuple[int, int], el: Element | None) -> Box:
    w, h = canvas()
    if el:
        p = CFG.crop_pad
        b = Box(el.box.x1 - p, el.box.y1 - p, el.box.x2 + p, el.box.y2 + p)
    else:
        cw, ch = CFG.point_crop
        b = Box(point[0] - cw // 2, point[1] - ch // 2, point[0] + cw // 2, point[1] + ch // 2)
    return Box(max(b.x1, 0), max(b.y1, 0), min(b.x2, w), min(b.y2, h))


def read_near(look: Look, point: tuple[int, int]) -> str:
    b = crop_box(point, None)
    return " ".join(e.text for e in look.elements if e.box.overlaps(b))


def spot_changed(before: Look, after: Look, point: tuple[int, int]) -> bool:
    """Pixels around the point changed. Catches password dots that OCR cannot read."""
    b = crop_box(point, None)
    a, z = (decode(x.png)[b.y1:b.y2, b.x1:b.x2] for x in (before, after))
    return float(np.mean(cv2.absdiff(a, z))) >= CFG.same_screen_mad


def screens_same(a: bytes, b: bytes) -> bool:
    ga, gb = (cv2.cvtColor(decode(p), cv2.COLOR_BGR2GRAY) for p in (a, b))
    return float(np.mean(cv2.absdiff(ga, gb))) < CFG.same_screen_mad


# %% [markdown]
# ## Safety & handoff (reused from discovery)
# Send guard, site lock, control tab, input helpers. The mismatch check compares against the inputs.

# %%
@dataclass
class ReplayState:
    """Working values for one run. Wiped in `replay`'s `finally` (R7)."""
    look: Look | None = None
    values: dict[str, str] = field(default_factory=dict)
    given: list[str] = field(default_factory=list)      # input values + human edits (mismatch check)
    outputs: dict[str, str] = field(default_factory=dict)
    allow_send: bool = False       # set only around a login click
    sent: bool = False             # a non-GET request went out during this action
    gated: bool = False            # this run sent something through the human gates (not the login)
    rung: str = ""                 # the rung that found the current step's target
    http: tuple[int, str] | None = None   # the last main-document response: (status, path)
    navs: int = 0                  # main-document responses so far (a same-URL reload is one too)
    verdict: str = ""              # what the send gate decided during the last action
    takeover: dict | None = None   # during a take-over only: page and send paths (3.6, no values)
    human: list[dict] = field(default_factory=list)    # one entry per take-over, for the result
    dropdowns: list[dict] = field(default_factory=list)  # read before a click (guard_send reads only this)
    step: int | None = None        # where the run is, for failure.json (len(steps) = the checkpoint)
    outcomes: list[dict] = field(default_factory=list)   # R17 rules for this run
    recoveries: int = 0            # re-logins done (at most one per run)
    action: str = ""


def url_path(url: str) -> str:
    """Path only: no query, no `;jsessionid`, so no values."""
    return urlparse(url).path.split(";")[0]


STATE = ReplayState()


def norm(text: str | None) -> str:
    return " ".join((text or "").casefold().split()).rstrip(".:!?").strip()


def is_sensitive(label: str) -> bool:
    return any(w in label.casefold() for w in CFG.sensitive_words)


SEND_GATE = asyncio.Lock()


DROPDOWNS_JS = """() => [...document.querySelectorAll('select')].map(s => ({
  value: s.value, text: s.options[s.selectedIndex]?.text.trim() ?? '',
  options: [...s.options].map(o => o.text.trim())}))"""


async def stash_dropdowns() -> list[dict]:
    """Before a click: a held send blocks `page.evaluate`, so guard_send only reads this stash."""
    try:
        STATE.dropdowns = await asyncio.wait_for(page.evaluate(DROPDOWNS_JS), CFG.page_s)
    except (asyncio.TimeoutError, PlaywrightError):
        STATE.dropdowns = []
    return STATE.dropdowns


def dropdown_options(fields: dict[str, str], keys: list[str]) -> list[list[str]]:
    free = [dict(d) for d in STATE.dropdowns]
    out = []
    for k in keys:
        hit = next((d for d in free if fields[k] and fields[k] in (d["value"], d["text"])), None)
        if hit:
            free.remove(hit)
        out.append([hide_secrets(o) for o in hit["options"]] if hit and len(hit["options"]) > 1 else [])
    return out


def mismatches(sent: dict[str, str]) -> list[str]:
    """Numbers being sent that the caller never gave (inputs or human edits)."""
    given = set(re.findall(r"\d+(?:\.\d+)?", " ".join(STATE.given)))
    norm_num = lambda n: n.rstrip("0").rstrip(".") if "." in n else n   # noqa: E731  10.00 == 10
    wanted = {norm_num(n) for n in given}
    return [k for k, v in sent.items() if not is_sensitive(k)
            and any(norm_num(n) not in wanted for n in re.findall(r"\d+(?:\.\d+)?", v))]


def _flat(obj: dict, pre: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out |= _flat(v, f"{pre}{k}.")
        elif not isinstance(v, list):
            out[f"{pre}{k}"] = "" if v is None else str(v)
    return out


def _json(body: str | None) -> dict | None:
    try:
        data = json.loads(body or "")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def sent_fields(req) -> dict[str, str]:
    data = _json(req.post_data)
    body = _flat(data) if data is not None else dict(parse_qsl(req.post_data or ""))
    return dict(parse_qsl(urlparse(req.url).query)) | body


def rebuilt(req, fields: dict[str, str]) -> tuple[str, str | None]:
    u = urlparse(req.url)
    query = {k: fields.get(k, v) for k, v in parse_qsl(u.query)}
    url = u._replace(query=urlencode(query)).geturl() if query else req.url
    data = _json(req.post_data)
    if data is not None:
        for key in _flat(data):
            *path, last = key.split(".")
            node = functools.reduce(lambda d, p: d[p], path, data)
            old, new = node.get(last), fields.get(key, "")
            is_num = isinstance(old, (int, float)) and not isinstance(old, bool)
            node[last] = type(old)(new) if is_num and new else new
        return url, json.dumps(data)
    form = dict(parse_qsl(req.post_data or ""))
    return url, (urlencode({k: fields.get(k, v) for k, v in form.items()}) if form else req.post_data)


def pretty(key: str) -> str:
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key.replace(".", " ").replace("_", " ")).split()
    return " ".join(words).capitalize()


def note_response(resp) -> None:
    """Keep the main document's HTTP status (not sub-resources, not iframes)."""
    if resp.request.is_navigation_request() and resp.frame is page.main_frame:
        STATE.http, STATE.navs = (resp.status, url_path(resp.url)), STATE.navs + 1


RAW_ERROR = re.compile(r'^\s*\{\s*"title"\s*:|"status"\s*:\s*[45]\d\d')


def error_page(after: str) -> "Stop | None":
    """R17 FAILED before any outcome rule: an HTTP error status, or a raw JSON error body."""
    if STATE.http and STATE.http[0] >= 400:
        return Stop("FAILED", f"page returned HTTP {STATE.http[0]}", "an HTTP 2xx page", STATE.http[1])
    if RAW_ERROR.search(after):
        return Stop("FAILED", "page is a raw error response", "a normal page", after[:200])
    return None


def note_takeover_send(url: str) -> None:
    if STATE.takeover is not None:
        STATE.takeover["sends"].append(url_path(url))


async def guard_send(route) -> None:
    """Every request that sends data (not GET) is held for two human gates (R6, R15)."""
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS"):
        return await route.continue_()
    STATE.sent = True
    note_takeover_send(req.url)
    if STATE.allow_send:
        return await route.continue_()
    STATE.gated = True
    human = STATE.takeover is not None     # the human's own send: they chose every value
    async with SEND_GATE:                  # never touch the page in here: a held request blocks it
        fields = sent_fields(req)
        original = dict(fields)
        if not human and (bad := mismatches(fields)):
            opts = dropdown_options(fields, bad)
            fixed = await CONTROL.form("You never gave these. Check or correct them:",
                                       [(pretty(k), False) for k in bad], [fields[k] for k in bad], opts)
            if not fixed or not all(fixed):
                STATE.verdict = f"STUCK: No value confirmed for {', '.join(bad)}. Nothing was sent."
                return await route.abort()
            fields.update(zip(bad, fixed))
            STATE.given.extend(fixed)
        shot = STATE.look.png if STATE.look else None    # never screenshot while a send is held
        while True:     # Gate 1: Approve, or Edit = back to the form with every value, then again
            sent = hide_secrets("\n".join(f"{pretty(k)}: {'******' if is_sensitive(k) else v}"
                                           for k, v in fields.items())[:1200])
            what = f"Sending to {urlparse(req.url).path}:\n{sent or '(no fields)'}"
            choice = await CONTROL.ask("Gate 1 of 2: confirm the details", what, "confirm",
                                       image=shot if fields == original else None)
            if choice == "approve":
                break
            if choice != "edit":
                STATE.verdict = "STUCK: the details were not confirmed. Nothing was sent."
                return await route.abort()
            editable = [k for k in fields if not is_sensitive(k)]
            opts = None if human else dropdown_options(fields, editable)
            new = await CONTROL.form("Edit the details, then Submit:",
                                     [(pretty(k), False) for k in editable],
                                     [fields[k] for k in editable], opts)
            if new:
                fields.update(zip(editable, new))
                STATE.given.extend(v for v in new if v)
        url, body = rebuilt(req, fields) if fields != original else (req.url, req.post_data)
        if await CONTROL.ask("Gate 2 of 2: confirm sending", f"{what}\nThis cannot be undone.",
                             "approve", image=shot if fields == original else None) != "approve":
            STATE.verdict = "DECLINED: a human said no at Gate 2. Nothing was sent."
            return await route.abort()
        STATE.verdict = "SENT: a human approved both gates."
        await route.continue_(url=url, post_data=body)


# %%
class SiteLock:
    """The site tab ignores all real input (CDP). Lifted only around our own action or a take-over."""

    def __init__(self, cdp: object) -> None:
        self._cdp = cdp

    async def set(self, locked: bool) -> None:
        await self._cdp.send("Input.setIgnoreInputEvents", {"ignore": locked})

    @contextlib.asynccontextmanager
    async def open(self):
        await self.set(False)
        try:
            yield
        finally:
            await self.set(True)


_CONTROLS = {
    "approve": "<button onclick=\"cuaReply('approve')\">Approve</button>"
               "<button onclick=\"cuaReply('reject')\">Reject</button>",
    "confirm": "<button onclick=\"cuaReply('approve')\">Approve</button>"
               "<button onclick=\"cuaReply('edit')\">Edit</button>",
    "takeover": "<button onclick=\"cuaReply('done')\">Done, hand back to replay</button>",
    "rescue": "<button onclick=\"cuaReply('takeover')\">Take over the site</button>"   # PLAN P2
              "<button onclick=\"cuaReply('stop')\">Stop the run</button>",
    "form": "<button onclick=\"cuaReply(JSON.stringify([...document.querySelectorAll('.f')]"
            ".map(e => e.value)))\">Submit</button><button onclick=\"cuaReply('')\">Skip</button>",
    "status": "",
}


class ControlWindow:
    """Our own page: the only place a human answers. Closing it fails closed (None)."""

    def __init__(self, win: object) -> None:
        self.win = win
        self._stack: list[tuple[asyncio.Future, tuple]] = []

    def on_reply(self, value: str | None) -> None:
        for fut, _ in (self._stack if value is None else self._stack[-1:]):
            if not fut.done():
                fut.set_result(value)

    async def show(self, title: str, details: str = "", mode: str = "status",
                   image: bytes | None = None, who: str = "replay", rows: str = "") -> None:
        if self.win.is_closed():
            self.on_reply(None)
            return
        tab = "Agent control" if mode == "status" else "▶ Agent control: your turn"
        try:
            await self.win.set_content(
                f"<title>{tab}</title>"
                "<style>body{font:15px sans-serif;max-width:640px;margin:24px auto;padding:0 16px}"
                "h3{margin:0 0 8px}.why{background:#fdecea;border-left:4px solid #c62828;"
                "padding:10px 12px;margin:0 0 14px;white-space:pre-line}"
                ".shot{display:block;max-width:560px;width:100%;margin:12px auto;border:1px solid #bbb}"
                "img{max-width:100%}button{margin:6px 6px 0 0;padding:8px 16px}"
                "textarea,.f{display:block;width:100%;box-sizing:border-box;padding:6px;margin:4px 0 12px}"
                ".who{color:#666;font-size:12px}</style>"
                f"<p class=who>In control: {who}</p><h3>{html.escape(title)}</h3>"
                + (f"<div class=why>{html.escape(details)}</div>" if details else "")
                + f"{_img(image, 'shot')}{rows}<div>{_CONTROLS[mode]}</div>")
        except Exception:
            self.on_reply(None)

    async def ask(self, title: str, details: str, mode: str, image: bytes | None = None,
                  who: str = "replay", rows: str = "") -> str | None:
        if self.win.is_closed():
            return None
        entry = (asyncio.get_running_loop().create_future(), (title, details, mode, image, who, rows))
        self._stack.append(entry)
        await self._front(entry[1])
        try:
            return await entry[0]
        finally:
            self._stack.remove(entry)
            if self.win.is_closed():
                pass
            elif self._stack:
                await self._front(self._stack[-1][1])
            else:
                await self.show("Replay is working")
                if not page.is_closed():
                    await page.bring_to_front()

    async def _front(self, q: tuple) -> None:
        if self.win.is_closed():
            self.on_reply(None)
            return
        await self.show(*q)
        if self.win.is_closed():
            self.on_reply(None)
            return
        target = page if q[2] == "takeover" else self.win
        if not target.is_closed():
            await target.bring_to_front()

    async def form(self, title: str, fields: list[tuple[str, bool]], values: list[str] | None = None,
                   options: list[list[str]] | None = None) -> list[str] | None:
        n = len(fields)
        rows = "".join(_row(i, label, masked, value, opts) for i, ((label, masked), value, opts)
                       in enumerate(zip(fields, values or [""] * n, options or [[]] * n)))
        answer = await self.ask(title, "Our code enters these into the site.", "form", rows=rows)
        return json.loads(answer) if answer else None


def _row(i: int, label: str, masked: bool, value: str, opts: list[str]) -> str:
    head = f"<label><b>{html.escape(label)}</b>"
    if opts:
        choices = "".join(f'<option{" selected" if o == value else ""}>{html.escape(o)}</option>'
                          for o in opts)
        return f"{head}<select class=f>{choices}</select></label>"
    kind = "password" if masked else "text"
    return f'{head}<input class=f type={kind} value="{html.escape(value, quote=True)}"></label>'


def _img(png: bytes | None, cls: str = "") -> str:
    return (f'<img class="{cls}" src="data:image/png;base64,{base64.b64encode(png).decode()}">'
            if png else "")


async def act(*steps) -> Look:
    """Unlock the site tab, run our own input steps, relock, settle, take a new look."""
    async with LOCK.open():
        for step in steps:
            await step()
    await page.wait_for_timeout(CFG.settle_ms)
    async with SEND_GATE:      # a send held for the human finishes first
        pass
    return await take_look()


def into_box(point: tuple[int, int], value: str) -> tuple:
    """Click the box, clear what is in it, type."""
    return (lambda: page.mouse.click(*to_page(point)), lambda: page.keyboard.press("ControlOrMeta+A"),
            lambda: page.keyboard.press("Backspace"), lambda: page.keyboard.type(value))


# D-B: the one non-visual exception. Sets only the <select> under (or next to) the point.
SELECT_AT_JS = """([x, y, want]) => {
  let el = document.elementFromPoint(x, y)?.closest('select');
  if (!el) {
    let best = 250;
    for (const s of document.querySelectorAll('select')) {
      const r = s.getBoundingClientRect();
      const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
      if (d < best) { best = d; el = s; }
    }
  }
  if (!el) return null;
  const opts = [...el.options].map(o => o.text.trim());
  if (want === null) return opts;
  const i = opts.indexOf(want);
  if (i < 0) return false;
  el.selectedIndex = i;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2, el.options[el.selectedIndex].text.trim()];
}"""


def field_box(look: Look, point: tuple[int, int]) -> Box:
    """The smallest drawn rectangle around the point (the input's own border), else the point crop."""
    edges = cv2.Canny(cv2.cvtColor(decode(look.png), cv2.COLOR_BGR2GRAY), 30, 90)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(c) for c in contours]
    boxes = [Box(x, y, x + w, y + h) for x, y, w, h in rects
             if w >= CFG.field_min[0] and h >= CFG.field_min[1]]
    hits = [b for b in boxes if b.contains(*point)]
    return min(hits, key=lambda b: (b.x2 - b.x1) * (b.y2 - b.y1)) if hits else crop_box(point, None)


def read_field(look: Look, point: tuple[int, int]) -> str:
    """Text inside the whole field: short values sit at its left edge, not near the centre (bug A)."""
    b = field_box(look, point)
    return " ".join(e.text for e in look.elements if e.box.overlaps(b))


async def choose_option(point: tuple[int, int], option: str, label: str = "") -> bool:
    """Select this exact live option; the dropdown's selected text and its OCR'd box confirm it."""
    at = await page.evaluate(SELECT_AT_JS, [*to_page(point), option])
    if not isinstance(at, list) or at[2] != option:
        return False
    await page.wait_for_timeout(CFG.settle_ms)
    look = await take_look()
    return typed_ok(read_field(look, (round(at[0] / look.scale), round(at[1] / look.scale))), at[2])


# %%
LOCK = SiteLock(await page.context.new_cdp_session(page))
await LOCK.set(True)
await page.unroute("**/*")
await page.route("**/*", guard_send)
if not getattr(page, "_cua_responses", False):     # once per page, even when this cell is re-run
    page.on("response", lambda r: note_response(r))  # network metadata only: the main document's status
    page._cua_responses = True
CONTROL = ControlWindow(control_page)
try:
    await control_page.expose_function("cuaReply", CONTROL.on_reply)
except Exception as e:
    if "already registered" not in str(e):
        raise
control_page.on("close", lambda _: CONTROL.on_reply(None))
await CONTROL.show("Replay is working")
if not page.is_closed():
    await page.bring_to_front()
print("site locked | control window open")

# %% [markdown]
# ## Artifact schema
# Schema: loaded from discovery's ## Save artifact (single source).

# %%
ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "notebooks/discovery/discovery.py").is_file())


def discovery_schema() -> dict:
    """Run the first cell of discovery's '## Save artifact' (the models) plus its typing/pydantic imports."""
    text = (ROOT / "notebooks/discovery/discovery.py").read_text()
    lines = text.splitlines()
    start = lines.index("# ## Save artifact")
    cell = [i + 1 for i, line in enumerate(lines) if line == "# %%" and i > start][:2]
    keep = [n for n in ast.parse(text).body if cell[0] < n.lineno < cell[1]
            or isinstance(n, ast.ImportFrom) and n.module in ("typing", "pydantic")]
    ns: dict = {"__name__": "discovery_schema"}      # pydantic resolves the models' module by it
    exec(compile(ast.Module(keep, []), "discovery.py", "exec"), ns)
    return ns


SCHEMA = discovery_schema()
Capability, Step, Target, TableCell = (SCHEMA[n] for n in ("Capability", "Step", "Target", "TableCell"))


# %% [markdown]
# ## Load & inputs
# YAML -> model, used exactly as discovery saved it. Refuse a wrong page size. One form before step 1
# asks every input; nothing from discovery is ever a value.

# %%
class Stop(Exception):
    """Ends the run with a status (R17). The reason never holds a value; `observed` is masked on save."""

    def __init__(self, status: str, reason: str, expected: str = "", observed: str = "") -> None:
        super().__init__(reason)
        self.status, self.reason, self.expected, self.observed = status, reason, expected, observed


PLACEHOLDER = re.compile(r"\{\{\s*(secret:)?(\w+)\s*\}\}")


def load_capability(path: str | Path) -> tuple[Capability, Path]:
    """The capability and the folder its crop paths are relative to."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    data.pop("outcomes", None)                  # replay's own optional key; the schema stays discovery's
    cap = Capability.model_validate(data)
    if tuple(cap.viewport) != CFG.viewport or cap.device_scale_factor != 1:
        raise Stop("FAILED", f"recorded at {cap.viewport} x{cap.device_scale_factor}, "
                             f"replay runs at {CFG.viewport} x1 (Q10)")
    if not host_allowed(cap.base_url):
        raise Stop("FAILED", "base_url host is not allowed")
    refs = PLACEHOLDER.findall(path.read_text())
    if unknown := {n for s, n in refs if not s} - {p.name for p in cap.inputs}:
        raise Stop("FAILED", f"undeclared inputs {sorted(unknown)}")
    if unset := sorted({n for s, n in refs if s and not SECRETS.get(n)}):
        raise Stop("FAILED", f"secrets not set in .env: {unset}")
    crops = [s.target.template for s in cap.steps if getattr(s, "target", None) and s.target.template]
    if lost := [c for c in crops if not (path.parent / c).is_file()]:
        raise Stop("FAILED", f"missing crops {lost}")
    return cap, path.parent


def load_outcomes(path: str | Path) -> list[dict]:
    """The capability's own `outcomes:` [{text, status, meaning}], else the generic defaults."""
    rules = yaml.safe_load(Path(path).read_text()).get("outcomes") or list(CFG.outcomes)
    if bad := [r for r in rules if r.get("status") not in ("BUSINESS_OUTCOME", "RECOVER", "FAILED")]:
        raise Stop("FAILED", f"outcomes with an unknown status: {bad}")
    return rules


def seen_outcome(before: str, after: str, rules: list[dict]) -> dict | None:
    """The first rule whose text (whole words, any case) appeared on screen with this step."""
    for rule in rules:
        hit = re.compile(rf"(?<!\w){re.escape(rule['text'])}(?!\w)", re.I)
        if hit.search(after) and not hit.search(before):
            return rule
    return None


def given_inputs(cap: Capability, inputs: dict[str, str]) -> dict[str, str]:
    """The caller's values, by the capability's own input names (any case). Any other key stops."""
    names = {p.name.casefold(): p.name for p in cap.inputs}
    if bad := [k for k in inputs if k.casefold() not in names]:
        accepts = ", ".join(p.name for p in cap.inputs) or "none"
        raise Stop("STUCK", f"not a permissible input: {', '.join(bad)}. Accepts: {accepts}.")
    return {names[k.casefold()]: v for k, v in inputs.items() if v}


def fill(text: str, values: dict[str, str]) -> str:
    """Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only when typed."""
    return PLACEHOLDER.sub(lambda m: m[0] if m[1] else values[m[2]], text)


def secret_name(value: str) -> str | None:
    m = PLACEHOLDER.fullmatch(value.strip())
    return m[2] if m and m[1] else None


def step_inputs(cap: Capability) -> list[str]:
    """Every `{{input}}` the steps use, in step order, once each."""
    found = (n for st in cap.steps for sec, n in PLACEHOLDER.findall(st.model_dump_json()) if not sec)
    return list(dict.fromkeys([*found, *(p.name for p in cap.inputs)]))


async def ask_inputs(cap: Capability, given: dict[str, str] | None = None) -> dict[str, str]:
    """R8: ONE form before step 1 for every input the caller did not give. Nothing is pre-filled."""
    given = dict(given or {})
    names = [n for n in step_inputs(cap) if n not in given]
    if not names:
        return given
    about = {p.name: p.description for p in cap.inputs}
    picks = {m[2] for st in cap.steps if st.action == "select" and (m := PLACEHOLDER.fullmatch(st.option))}
    rows = [(f"{n}: {about.get(n, '')}" + (" (must match an option on the page)" if n in picks else ""),
             is_sensitive(n)) for n in names]
    got = await CONTROL.form("Replay needs these inputs:", rows) or [""] * len(names)
    if blank := [n for n, v in zip(names, got) if not v]:
        raise Stop("STUCK", f"inputs not given: {blank}")
    return given | dict(zip(names, got))


async def ask_option(cap: Capability, name: str, options: list[str]) -> str:
    """The one mid-run prompt: the given value is not a live option. Choose one, blank first."""
    about = next((p.description for p in cap.inputs if p.name == name), "")
    got = await CONTROL.form("That value is not an option here:", [(f"{name}: {about}", False)], [""],
                             [["", *options]])
    if not got or got[0] not in options:
        raise Stop("STUCK", f"no option chosen for {name}")
    return got[0]


# %% [markdown]
# ## Locate (rungs)
# Rung 1 OCR text, rung 2 label + offset, rung 3 picture, or a table cell. Never raw x,y.

# %%
def same_text(seen: str, want: str) -> bool:
    """Exact for anything with a digit (13344 is not 13345); fuzzy for words (PLAN P3)."""
    a, b = norm(seen), norm(want)
    if a == b or re.search(r"\d", b):
        return a == b
    return difflib.SequenceMatcher(None, a, b).ratio() >= CFG.fuzzy


def typed_ok(seen: str, want: str) -> bool:
    """Bug B: the value is one of the OCR words. Digits exact ($10.00 is 10.00); words fuzzy (llinois)."""
    words, n = norm(seen).replace("$", "").replace(",", "").split(), len(norm(want).split())
    runs = [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
    return any(same_text(r, want.replace("$", "").replace(",", "")) for r in runs)


def same_label(seen: str, label: str) -> bool:
    """Rung 2 anchors only. Discovery saves labels cleaned ('to account #'); live OCR may merge the
    label with its field's value ('to account #[16785'). Strip `[ ] |`, then a label at the start counts."""
    a, b = norm(re.sub(r"[\[\]|]", " ", seen)), norm(re.sub(r"[\[\]|]", " ", label))
    return bool(b) and a.startswith(b) or same_text(a, b)


def find_text(look: Look, text: str, ordinal: int = 1, match=same_text) -> Element | None:
    hits = [e for e in look.elements if match(e.text, text)]
    return hits[ordinal - 1] if len(hits) >= ordinal else None


def find_template(img: np.ndarray, tpl: np.ndarray) -> tuple[int, int] | None:
    """Centre of the one clear best match; two near-equal peaks count as a miss."""
    h, w = tpl.shape[:2]
    if h > img.shape[0] or w > img.shape[1]:
        return None
    res = np.nan_to_num(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED), nan=-1.0)
    _, best, _, (x, y) = cv2.minMaxLoc(res)
    res[max(y - h // 2, 0):y + h // 2 + 1, max(x - w // 2, 0):x + w // 2 + 1] = -1
    if best < CFG.template_threshold or cv2.minMaxLoc(res)[1] > best - CFG.template_margin:
        return None
    return x + w // 2, y + h // 2


def read_cell(look: Look, cell: TableCell, values: dict[str, str]) -> Element | None:
    """Q8: the element on the row-key's row, under the column header."""
    key, head = find_text(look, fill(cell.row_key, values)), find_text(look, cell.column)
    if not key or not head:
        return None
    return next((e for e in look.elements if e is not key and e.box.y1 < key.box.y2
                 and key.box.y1 < e.box.y2 and head.box.x1 < e.box.x2 and e.box.x1 < head.box.x2), None)


def anchor_point(look: Look, a, values: dict[str, str]) -> tuple[int, int] | None:
    """Rung 2's point: the anchor label's centre plus the recorded offset."""
    el = find_text(look, fill(a.label, values), a.ordinal, same_label) if a else None
    return (el.box.center[0] + a.offset[0], el.box.center[1] + a.offset[1]) if el else None


def text_hit(look: Look, text: str, ordinal: int,
             near: tuple[int, int] | None) -> tuple[tuple[int, int], str] | None:
    """Rung 1. The same text twice (a menu link and a page heading): the copy nearest the anchor's
    point wins; none near it = no hit, so rung 2 (the anchor itself) decides."""
    hits = [e for e in look.elements if same_text(e.text, text)]
    if len(hits) < 2 or near is None:
        el = hits[ordinal - 1] if len(hits) >= ordinal else None
        return (el.box.center, "rung1") if el else None
    best = min(hits, key=lambda e: math.dist(e.box.center, near))
    if math.dist(best.box.center, near) > CFG.near_px:
        return None
    by_ordinal = hits[ordinal - 1] if len(hits) >= ordinal else None
    return best.box.center, "rung1" if best is by_ordinal else "rung1+anchor"


def locate(look: Look, target: Target, values: dict[str, str],
           crops: Path) -> tuple[tuple[int, int], str] | None:
    """(point, rung) from the first rung that hits, or None."""
    if (c := target.table_cell) and (el := read_cell(look, c, values)):
        return el.box.center, "table"
    near = anchor_point(look, target.anchor, values)
    if (t := target.ocr_text) and (hit := text_hit(look, fill(t.text, values), t.ordinal, near)):
        return hit
    if near:
        return near, "rung2"
    if target.template and (p := find_template(decode(look.png), cv2.imread(str(crops / target.template)))):
        return p, "rung3"
    return None


async def find(target: Target, crops: Path) -> tuple[tuple[int, int], str] | None:
    """All rungs miss -> scroll down and try again (Q13), up to `CFG.scroll_retries`."""
    for n in range(CFG.scroll_retries + 1):
        look = STATE.look if n == 0 else await act(lambda: page.mouse.wheel(0, CFG.scroll_px))
        if hit := locate(look, target, STATE.values, crops):
            return hit if n == 0 else (hit[0], f"{hit[1]}+scroll{n}")
    return None


# %% [markdown]
# ## Steps
# One function per action. Each acts through discovery's `act` and returns whether the OCR check passed.

# %%
async def shows(text: str) -> bool:
    """R5: bounded OCR poll until the text is on screen."""
    deadline = time.monotonic() + CFG.check_s
    while norm(fill(text, STATE.values)) not in norm(STATE.look.text):
        if time.monotonic() > deadline:
            return False
        await page.wait_for_timeout(CFG.poll_ms)
        await take_look()
    return True


def site_url(base_url: str, path: str) -> str:
    """Like a browser: '/parabank/x.htm' is from the site root, 'x.htm' is under base_url."""
    return urljoin(base_url + "/", path)


async def do_navigate(step: Step, point, cap: Capability) -> bool:
    url = site_url(cap.base_url, fill(step.path, STATE.values))
    if not host_allowed(url):
        raise Stop("FAILED", "navigate leaves the allowed site")
    await page.goto(url)
    await take_look()
    return True


async def do_click(step: Step, point: tuple[int, int], cap: Capability) -> bool:
    before, navs = STATE.look, STATE.navs
    el = element_at(before, point)
    STATE.allow_send = norm(el.text if el else "") in CFG.login_words     # R6: login is exempt
    await stash_dropdowns()
    try:
        await act(lambda: page.mouse.click(*to_page(point)))
    finally:
        STATE.allow_send = False
    if not host_allowed(page.url):
        await page.go_back()
        raise Stop("FAILED", "the click left the allowed site")
    if STATE.navs > navs:            # the page loaded again (even the same URL, the same screen)
        return True
    return await settled_change(before)


def changed(before: Look, after: Look) -> bool:
    """The pixels moved, or new text is on screen: a small answer ('Transfer Complete!') can sit
    under the whole-screen pixel threshold, but OCR still sees it."""
    return not screens_same(before.png, after.png) or norm(before.text) != norm(after.text)


async def settled_change(before: Look) -> bool:
    """Bug D: a send can land after the settle. Poll until the screen changes, then holds still.
    A send held at the gates is never judged: the window starts again once the human answered."""
    deadline, prev = time.monotonic() + CFG.check_s, STATE.look
    while time.monotonic() < deadline:
        await page.wait_for_timeout(CFG.poll_ms)
        if SEND_GATE.locked():                # the gates took the send after `act`'s own wait
            async with SEND_GATE:
                pass
            deadline = time.monotonic() + CFG.check_s
        look = await take_look()
        if changed(before, look) and not changed(prev, look):
            return True
        prev = look
    return changed(before, STATE.look)


async def do_type(step: Step, point: tuple[int, int], cap: Capability) -> bool:
    before, name = STATE.look, secret_name(step.value)
    value = SECRETS[name] if name else fill(step.value, STATE.values)
    after = await act(*into_box(point, value))
    if not name:        # OCR misses a lone character ('1'): then the field's own pixels must change
        short = len(value.strip()) <= CFG.short_value
        return typed_ok(read_field(after, point), value) or short and spot_changed(before, after, point)
    if is_sensitive(name) and value in read_field(after, point):
        STATE.look = None
        raise Stop("FAILED", f"secret '{name}' shows as plain text")
    return spot_changed(before, after, point)


async def do_select(step: Step, point: tuple[int, int], cap: Capability) -> bool:
    options = await page.evaluate(SELECT_AT_JS, [*to_page(point), None])
    if not isinstance(options, list) or not options:
        return False
    m = PLACEHOLDER.fullmatch(step.option.strip())
    want = STATE.values.get(m[2], "") if m else step.option
    if m and want not in options:
        want = STATE.values[m[2]] = await ask_option(cap, m[2], options)
        STATE.given.append(want)
    return await choose_option(point, want)


async def do_scroll(step: Step, point, cap: Capability) -> bool:
    await act(lambda: page.mouse.wheel(0, CFG.scroll_px if step.direction == "down" else -CFG.scroll_px))
    return True


# Replay's own strict value types (the recorder's currency accepts any integer, e.g. an account id).
# Keep identical to discovery's SHAPES (tests/replay/test_extract_pattern.py checks it).
SHAPES = {
    "phone": r"\+?\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}",
    "currency": r"-?\$-?[\d,]*\d(?:\.\d{2})?|-?[\d,]*\d\.\d{2}",      # a `$`, or exactly 2 decimals
    "date": r"\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}",
    "integer": r"-?\d+",
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "id": r"[A-Za-z]*\d[\w-]*",
}
TYPES = {"string": r"\S.*", "number": r"-?[\d,]*\.?\d+", "boolean": r"true|false|yes|no", **SHAPES}


def is_type(text: str, kind: str) -> bool:
    return kind in TYPES and bool(re.fullmatch(TYPES[kind], text.strip(), re.I))


RUNGS = {"table": "table_cell", "rung1": "ocr_text", "rung2": "anchor", "rung3": "template"}


def next_rung(target: Target, rung: str) -> tuple[tuple[int, int], str] | None:
    """Where the rungs after `rung` point (e.g. the anchor after a wrong table cell), if any."""
    order = list(RUNGS.values())
    done = order[:order.index(RUNGS[rung.split("+")[0]]) + 1] if rung.split("+")[0] in RUNGS else order
    rest = target.model_copy(update=dict.fromkeys(done))
    return locate(STATE.look, rest, STATE.values, None) if any(getattr(rest, k) for k in order) else None


def value_of(text: str, kind: str, pattern: str | None) -> str | None:
    """The box's value: with a saved `pattern`, its first match inside the box; else the whole box.
    Either way it must be the output's type."""
    if pattern:
        hit = re.search(pattern, text)
        text = hit.group() if hit else ""
    return text.strip() if is_type(text, kind) else None


async def do_extract(step: Step, point: tuple[int, int], cap: Capability) -> bool:
    """Read the value at the point. A wrong value tries the next rung once, then stops: never guess."""
    kind = next(o.type for o in cap.outputs if o.name == step.save_as)
    pattern = getattr(step, "pattern", None)          # optional: older artifacts have none
    el = element_at(STATE.look, point)
    if el and value_of(el.text, kind, pattern) is None and (hit := next_rung(step.target, STATE.rung)):
        el, STATE.rung = element_at(STATE.look, hit[0]) or el, hit[1]
    if el is None:
        return False
    if (value := value_of(el.text, kind, pattern)) is None:
        raise Stop("STUCK", f"{step.save_as} is not a {kind}", kind, hide_secrets(el.text))
    STATE.outputs[step.save_as] = value
    return True


ACTIONS = {"navigate": do_navigate, "click": do_click, "type": do_type, "select": do_select,
           "scroll": do_scroll, "extract": do_extract}

# %% [markdown]
# ## Replay engine
# Walk the steps. Retry a failed check once, never a send or a secret. A human rescues or stops it.

# %%
@dataclass(frozen=True)
class ReplayResult:
    status: str               # SUCCESS | BUSINESS_OUTCOME | DECLINED | STUCK | FAILED (R17)
    outputs: dict[str, str]
    drift: list[dict]         # per step: rung, point, attempt. No values (R18)
    reason: str = ""
    human: list[dict] = field(default_factory=list)   # R17: take-overs; [] = unattended
    failure: dict | None = None   # {step, action, expected, observed} when not SUCCESS (R17 Failure)
    recoveries: int = 0           # R17 recoverable errors fixed by a re-login
    cleanup: str = ""             # "" = no cleanup steps (or never logged in) | "done" | "failed: <why>"

    @property
    def outputs_line(self) -> str:
        head = "outputs" if self.status == "SUCCESS" else "partial outputs (run did not succeed)"
        return f"{head}: {self.outputs}"

    @property
    def summary(self) -> str:
        if not self.human:
            return self.status
        steps = [str(h["step"] + 1) for h in self.human]
        return f"{self.status} (human intervened at step{'s' if len(steps) > 1 else ''} {', '.join(steps)})"


async def snap() -> bytes | None:
    """Evidence screenshot. A held form POST blocks `page.screenshot()`: give up, never crash."""
    try:
        return (await asyncio.wait_for(take_look(), CFG.snap_s)).png
    except (asyncio.TimeoutError, PlaywrightError):
        return None


def takeover_text() -> str:
    return ("Do this step in the site tab. When you're done, click the Agent hand-back icon in the "
            "browser toolbar (pin it once from the puzzle-piece menu), or Done in the Agent control tab.")


async def ext_call(script: str) -> object:
    """R19: one bounded call into the hand-back extension's service worker, never the site page.
    No extension, or one that errors or hangs, gives None: the take-over carries on without it."""
    if EXT is None:
        return None
    try:
        return await asyncio.wait_for(EXT.evaluate(script), CFG.ext_s)
    except (asyncio.TimeoutError, PlaywrightError):
        return None


async def button_clicked() -> None:
    """Returns once the toolbar button's click count rises above where it was at the start."""
    base = await ext_call("self.handbackClicked || 0")
    while True:
        await asyncio.sleep(CFG.ext_poll_s)
        n = await ext_call("self.handbackClicked || 0")
        if base is None:
            base = n
        elif n is not None and n > base:
            return


@contextlib.asynccontextmanager
async def handback_button():
    """Badge YOU while the human is in control; yields the task a toolbar click completes."""
    await ext_call("setMode('YOU')")
    clicked = asyncio.ensure_future(button_clicked())
    try:
        yield clicked
    finally:
        clicked.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await clicked
        await ext_call("setMode('AI')")


async def hand_back(button: asyncio.Future) -> None:
    """Done on the toolbar button or in the take-over panel hands back. No reminders in between."""
    panel = asyncio.ensure_future(CONTROL.ask("You are in control", takeover_text(), "takeover", who="human"))
    try:
        await asyncio.wait({panel, button}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        panel.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await panel


async def rescue(i: int, step: Step, why: str) -> dict:
    """R8: the help panel. Take over (the human does this step) or stop. Returns the evidence (3.6):
    screenshots at start and hand-back, page and send paths. Never typed values; never new steps."""
    choice = await CONTROL.ask(f"Replay needs help at step {i + 1} ({step.action})", why, "rescue",
                               image=STATE.look.drawn if STATE.look else None)
    if choice != "takeover":
        raise Stop("STUCK", why)
    start, acts = await snap(), {"pages": [], "sends": []}

    def visited(frame) -> None:
        if frame is page.main_frame:
            acts["pages"].append(url_path(frame.url))

    STATE.takeover = acts
    page.on("framenavigated", visited)
    try:
        async with LOCK.open(), handback_button() as button:   # the human's sends still meet both gates
            await hand_back(button)
    finally:
        page.remove_listener("framenavigated", visited)
        STATE.takeover = None
    STATE.human.append({"step": i, "reason": why, "actions": acts})
    try:                         # a send the human made is gated and released before hand-back
        await asyncio.wait_for(SEND_GATE.acquire(), CFG.gate_s)
    except asyncio.TimeoutError:
        raise Stop("STUCK", "the take-over's send is still waiting at the gates") from None
    SEND_GATE.release()
    if not host_allowed(page.url):
        raise Stop("FAILED", "the take-over left the allowed site")
    end = await snap()
    return {"actions": acts, "shots": {"start": start, "end": end}}


def login_steps(cap: Capability) -> list:
    """The steps up to and including the first click, when a secret is typed before it."""
    head = next((cap.steps[:n + 1] for n, s in enumerate(cap.steps) if s.action == "click"), [])
    return head if starts_with_login(cap) else []


def login_came_back(cap: Capability, i: int, before: str, after: str) -> bool:
    """Mid-run, the login form's label appeared with this step: the site logged the run out."""
    login = login_steps(cap)
    anchor = login[0].target.anchor if login else None
    label = norm(anchor.label) if anchor else ""
    return i >= len(login) > 0 and bool(label) and label not in norm(before) and label in norm(after)


async def judge(i: int, before: str, cap: Capability, crops: Path, drift: list[dict]) -> bool:
    """R17 after a step. BUSINESS_OUTCOME / FAILED stop; RECOVER logs in again once. True = retry."""
    after = STATE.look.text if STATE.look else ""
    if err := error_page(after):          # BUSINESS_OUTCOME only ever comes from a normal page
        raise err
    rule = seen_outcome(before, after, STATE.outcomes)
    if rule is None and login_came_back(cap, i, before, after):
        rule = {"text": "login page", "status": "RECOVER", "meaning": "the site logged the run out"}
    if rule is None:
        return False
    if rule["status"] == "RECOVER" and not STATE.sent and STATE.recoveries == 0:
        STATE.recoveries += 1
        drift.append({"step": i, "action": "relogin", "rung": "recover", "outcome": rule["text"]})
        for j, s in enumerate(login_steps(cap)):
            await run_step(j, s, cap, crops, drift)
        STATE.step, STATE.action = i, cap.steps[i].action
        return True
    status = "BUSINESS_OUTCOME" if rule["status"] == "BUSINESS_OUTCOME" else "FAILED"
    raise Stop(status, rule["meaning"], f"step {i + 1} without '{rule['text']}'", after[:200])


async def run_step(i: int, step: Step, cap: Capability, crops: Path, drift: list[dict]) -> None:
    STATE.step, STATE.action = i, step.action
    attempt = 0
    while attempt < 2:
        attempt += 1
        target = getattr(step, "target", None)
        if (hit := await find(target, crops) if target else (None, "-")) is None:
            break
        STATE.sent, STATE.verdict, STATE.rung = False, "", hit[1]
        before = STATE.look.text if STATE.look else ""
        ok = await ACTIONS[step.action](step, hit[0], cap)
        drift.append({"step": i, "action": step.action, "rung": hit[1], "point": hit[0], "attempt": attempt,
                      "checked": ok})
        status = STATE.verdict.split(":")[0]
        if status in ("STUCK", "DECLINED"):
            raise Stop(status, STATE.verdict)
        if await judge(i, before, cap, crops, drift):
            attempt -= 1                          # the re-login does not use up the step's retry
            continue
        if ok:
            return
        if STATE.sent or secret_name(getattr(step, "value", "")):
            break                             # R15/D26: a send is never retried; R5: nor a secret
        await take_look()
    evidence = await rescue(i, step, "target not found" if hit is None else "the step's check failed")
    drift.append({"step": i, "action": step.action, "rung": "human", **evidence})


def took_over_to_checkpoint(i: int, cap: Capability, before: str) -> bool:
    """Step i ended in a take-over, and the human went on to the final screen: the checkpoint text
    is on screen now and was not before the take-over."""
    want = norm(fill(cap.checkpoint, STATE.values))
    helped = bool(STATE.human) and STATE.human[-1]["step"] == i
    return helped and want not in norm(before) and STATE.look is not None and want in norm(STATE.look.text)


def is_cleanup(step: Step) -> bool:
    return bool(getattr(step, "cleanup", False))


async def walk(cap: Capability, crops: Path, drift: list[dict]) -> ReplayResult:
    """The main steps (every step not marked cleanup), then the checkpoint and the outputs."""
    reached = False           # a human's take-over already got to the checkpoint: nothing left to do
    for i, step in enumerate(cap.steps):
        if is_cleanup(step):
            continue
        if reached:
            drift.append({"step": i, "action": step.action, "rung": "skipped"})
            continue
        before = STATE.look.text if STATE.look else ""
        await run_step(i, step, cap, crops, drift)
        reached = took_over_to_checkpoint(i, cap, before)
    STATE.step, STATE.action = len(cap.steps), "checkpoint"
    missing = sorted({o.name for o in cap.outputs} - set(STATE.outputs))
    reason = ""
    if not await shows(cap.checkpoint):
        if not read_only_done(cap, missing):
            raise Stop("FAILED", "checkpoint text not on the final screen", cap.checkpoint,
                       STATE.look.text[:200] if STATE.look else "")
        reason = "checkpoint looked for after cleanup; all outputs read"
    if missing:
        raise Stop("FAILED", f"outputs not read: {missing}")
    return ReplayResult("SUCCESS", dict(STATE.outputs), drift, reason, list(STATE.human),
                        recoveries=STATE.recoveries)


def read_only_done(cap: Capability, missing: list[str]) -> bool:
    """R17: a read-only run whose last main step read the last output, and every output was read.
    Its checkpoint was picked after the cleanup (e.g. the login page after Log Out): accept it."""
    main = [s for s in cap.steps if not is_cleanup(s)]
    last_reads = bool(main) and main[-1].action == "extract"
    return bool(cap.outputs) and not missing and not STATE.gated and last_reads


async def run_cleanup(cap: Capability, crops: Path, drift: list[dict]) -> str:
    """Cleanup steps (e.g. Log Out): best-effort, one retry, no rescue panel. Never changes the status."""
    steps = [(i, s) for i, s in enumerate(cap.steps) if is_cleanup(s)]
    if not steps:
        return ""
    for i, step in steps:
        for attempt in (1, 2):
            try:
                hit = await find(step.target, crops) if getattr(step, "target", None) else (None, "-")
                ok = hit is not None and await ACTIONS[step.action](step, hit[0], cap)
            except Stop as s:
                return f"failed: {s.reason}"
            drift.append({"step": i, "action": step.action, "rung": hit[1] if hit else "miss",
                          "point": hit[0] if hit else None, "attempt": attempt, "checked": ok,
                          "cleanup": True})
            if ok:
                break
            if STATE.sent or attempt == 2:
                return "failed: target not found" if hit is None else "failed: the step's check failed"
            await take_look()
    return "done"


async def stopped(s: Stop, drift: list[dict]) -> ReplayResult:
    """A run that stopped: its status, the failure detail (R17) and the final screen for evidence."""
    LAST_RUN["final"] = await snap()
    failure = {"step": STATE.step, "action": STATE.action, "expected": s.expected,
               "observed": hide_secrets(s.observed or s.reason)}
    return ReplayResult(s.status, dict(STATE.outputs), drift, hide_secrets(s.reason), list(STATE.human),
                        failure, STATE.recoveries)


async def finish(cap: Capability, crops: Path, drift: list[dict]) -> ReplayResult:
    """Main steps -> checkpoint -> outputs, then the cleanup steps, ALWAYS (the run is logged in)."""
    try:
        res = await walk(cap, crops, drift)
    except Stop as s:
        res = await stopped(s, drift)
    finally:
        done = await run_cleanup(cap, crops, drift)
    return replace(res, cleanup=hide_secrets(done))


def starts_with_login(cap: Capability) -> bool:
    """A secret is typed before the first click: the capability logs in itself."""
    for s in cap.steps:
        if s.action == "click":
            return False
        if s.action == "type" and secret_name(s.value):
            return True
    return False


async def open_start(cap: Capability) -> None:
    if starts_with_login(cap):
        await page.context.clear_cookies()      # start logged out, as the recording did
    await page.goto(cap.base_url)
    shot = decode(await page.screenshot())
    if (shot.shape[1], shot.shape[0]) != tuple(cap.viewport):       # R3: no scaling
        raise Stop("FAILED", f"screenshot is {shot.shape[1]}x{shot.shape[0]}, expected {cap.viewport}")
    await take_look()


async def replay(path: str, inputs: dict[str, str] | None = None) -> ReplayResult:
    global STATE
    drift: list[dict] = []
    LAST_RUN.update(values=set(), final=None)
    try:
        cap, crops = load_capability(path)
        STATE.outcomes = load_outcomes(path)
        given = given_inputs(cap, inputs or {})     # an unknown key stops before the site opens
        await open_start(cap)
        STATE.values = await ask_inputs(cap, given)
        STATE.given = list(STATE.values.values())
        return await finish(cap, crops, drift)      # from here on, cleanup always runs
    except Stop as s:
        return await stopped(s, drift)
    except ValidationError as e:
        where = e.errors()[0]
        return ReplayResult("FAILED", {}, drift, f"invalid capability at {where['loc']}: {where['msg']}")
    finally:
        LAST_RUN["values"] = {v for v in (*STATE.values.values(), *STATE.given) if v}   # masking only
        STATE = ReplayState()      # R7: nothing kept

# %% [markdown]
# ## Evidence
# One folder per run under `evidence/replay/` (spec 3.5, 6.3): summary, drift, failure, the final
# screen, take-over shots and a copy of the capability. Every value the human gave and every secret
# is masked: `***` in text, a black box over its OCR text in a PNG. Same approach as discovery.

# %%
LAST_RUN: dict = {"values": set(), "final": None}   # the last run's mask set + final shot; memory only
NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?(?!\w)")   # whole numbers only: never 'rung1'


def _num(text: str) -> str:
    n = text.lstrip("$").replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def redactor(values: set[str]):
    """text -> text with every value masked. Numbers match however they are written
    ('100000' = '$100,000.00'); words match whole, case-insensitively ('IL' never hits 'Bill')."""
    nums = {_num(v) for v in values if NUMBER.fullmatch(v.strip())}
    words = sorted((v for v in values if len(v.strip()) > 1 and not NUMBER.fullmatch(v.strip())),
                   key=len, reverse=True)
    alts = "|".join(rf"(?<!\w){re.escape(w.strip())}(?!\w)" for w in words)
    word_re = re.compile(alts, re.I) if words else None

    def redact(text: str) -> str:
        text = NUMBER.sub(lambda m: "***" if _num(m.group()) in nums else m.group(), text)
        return word_re.sub("***", text) if word_re else text
    return redact


def mask_png(png: bytes, redact) -> bytes:
    """Black out every OCR box whose text holds a run value. A clean image is written as is."""
    img = decode(png)
    hits = [box for text, box in ocr(img) if redact(text) != text]
    for b in hits:
        img[b.y1:b.y2, b.x1:b.x2] = 0
    return encode(img) if hits else png


def _clean(obj, redact):
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: _clean(v, redact) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v, redact) for v in obj]
    return obj


def _png(path: Path, png: bytes | None, redact) -> str | None:
    if not png:
        return None
    path.write_bytes(mask_png(png, redact))
    return path.name


def save_evidence(result: ReplayResult, cap_path: str | Path,
                  out_dir: Path = ROOT / "evidence" / "replay") -> Path:
    """Write the last run's evidence, masked. Call right after `replay`, successful or not."""
    redact = redactor(LAST_RUN["values"] | {v for v in SECRETS.values() if v})
    cap_path = Path(cap_path)
    name = yaml.safe_load(cap_path.read_text()).get("name", cap_path.stem)
    run = Path(out_dir) / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{name}"
    run.mkdir(parents=True, exist_ok=True)
    lines = []
    for row in result.drift:
        row = dict(row)
        if "shots" in row:
            n, shots = sum(1 for x in lines if '"shots"' in x), row["shots"]
            row["shots"] = {part: _png(run / f"take_over_{n}_{part}.png", shots.get(key), redact)
                            for part, key in (("before", "start"), ("after", "end"))}
        lines.append(json.dumps(_clean(row, redact), default=str))
    (run / "drift.jsonl").write_text("\n".join(lines) + "\n")
    summary = {"status": result.status, "reason": result.reason, "summary": result.summary,
               "outputs": {k: "***" for k in result.outputs}, "human": result.human,
               "failing_step": result.failure["step"] if result.failure else None, "cleanup": result.cleanup}
    (run / "summary.json").write_text(json.dumps(_clean(summary, redact), indent=2) + "\n")
    if result.failure:
        (run / "failure.json").write_text(json.dumps(_clean(result.failure, redact), indent=2) + "\n")
    _png(run / "final.png", LAST_RUN["final"], redact)
    (run / "capability.yaml").write_text(cap_path.read_text())
    return run


# %% [markdown]
# ## Run
# Replay a saved capability. Outputs go to the caller only; the drift log holds rungs, never values.

# %%
cap_path = ROOT / "notebooks" / "discovery" / "artifacts" / "visual" / "get_all_account_balances.yaml"
result = await replay(str(cap_path), inputs={})   # e.g. {"amount": "10"}; the rest is asked
print("capability:", cap_path)
print("status:", result.summary, result.reason, f"| recoveries: {result.recoveries}",
      f"| cleanup: {result.cleanup or 'none'}")
print(result.outputs_line)
for row in result.drift:
    print({k: v for k, v in row.items() if k != "shots"})
print(save_evidence(result, cap_path))

# %%

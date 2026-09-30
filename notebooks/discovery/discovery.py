# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: BankerAgent (.venv)
#     language: python
#     name: banker-agent
# ---

# %% [markdown]
# # Visual discovery
# The agent sees only a screenshot with numbered OCR boxes. A human answers in a control window.

# %% [markdown]
# ## Setup
# Imports, `.env`, and the model from the Iliad gateway.

# %%
import asyncio
import base64
import contextlib
import functools
import html
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

import cv2
import numpy as np
import yaml
from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rapidocr import RapidOCR

from cua.models import make_chat_model
from cua.recorder import value_matches_type

load_dotenv(override=True)
MODEL = make_chat_model("sonnet")
print("model:", MODEL.model)

# %% [markdown]
# ## Config & secrets
# Every ParaBank value lives in this cell. Secrets are read from `.env`; only their names are shown.

# %%
START_URL = "https://parabank.parasoft.com/parabank/"       # the only site input: where to begin
BASE_URL = START_URL.rstrip("/")
ALLOWED_HOSTS = {urlparse(START_URL).hostname}
SECRET_ENV = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}
SECRETS = {name: os.getenv(env, "") for name, env in SECRET_ENV.items()}


def host_allowed(url: str) -> bool:
    return url == "about:blank" or urlparse(url).hostname in ALLOWED_HOSTS


@dataclass(frozen=True)
class Config:
    viewport: tuple[int, int] = (1280, 800)       # Q10: fixed page size, same at discovery and replay
    ocr_min_score: float = 0.5
    scroll_px: int = 600
    same_screen_mad: float = 1.0      # mean pixel diff below this = "nothing changed"
    crop_pad: int = 6
    point_crop: tuple[int, int] = (160, 34)
    settle_ms: int = 600
    send_wait_ms: int = 8000          # after an approved send: how long to wait for the response
    snap_ms: int = 3000               # an evidence screenshot gives up after this, never crashes a run
    handback_s: int = 120             # after Done: how long a send the human started may stay held
    ext_s: float = 1.0                # any one call into the hand-back extension gives up after this
    ext_poll_s: float = 0.5           # take-over: how often the toolbar button's clicks are read
    deny_words: frozenset[str] = frozenset()      # refused outright (D33)
    sensitive_words: frozenset[str] = frozenset({"password", "ssn", "social"})  # D34
    login_words: frozenset[str] = frozenset()
    login_failure_texts: tuple[str, ...] = ()
    login_limit: int = 3                          # D69
    repeat_limit: int = 3
    unsure_limit: int = 3                         # failed tool results in a row = the agent is unsure
    step_budget: int = 40                         # tool calls per run before it counts as a loop


CFG = Config(
    deny_words=frozenset({"register", "lookup", "admin"}),
    login_words=frozenset({"log in"}),

    login_failure_texts=("could not be verified", "user does not exist",
                         "invalid username or password", "please enter a username and password"),
)
print("base:", BASE_URL, "| secrets set:", sorted(n for n, v in SECRETS.items() if v))

# %% [markdown]
# ## Browser
# One visible Chromium at a fixed page size and zoom (Q10), the same at discovery and replay:
# the site tab plus our own "Agent control" tab, which comes to the front when a human is needed.
# It loads our hand-back extension (Q16): a toolbar button only, no content scripts, no host
# access, so it never touches any site. `EXT` is its service worker, or None if it did not load.

# %%
if "page" not in globals():
    pw = await async_playwright().start()
    w, h = CFG.viewport
    ext_dir = next(p / "extensions/handback" for p in (Path.cwd(), *Path.cwd().parents)
                   if (p / "extensions/handback/manifest.json").is_file())
    context = await pw.chromium.launch_persistent_context(
        tempfile.mkdtemp(prefix="cua-discovery-"), headless=False, viewport={"width": w, "height": h},
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
await page.goto(START_URL)
shot = cv2.imdecode(np.frombuffer(await page.screenshot(), np.uint8), cv2.IMREAD_COLOR)
if (shot.shape[1], shot.shape[0]) != CFG.viewport:        # Q10: refuse rather than record a mismatch
    raise RuntimeError(f"screenshot is {shot.shape[1]}x{shot.shape[0]}, expected {CFG.viewport}")
print("opened:", page.url, "| page", CFG.viewport)

# %% [markdown]
# ## Vision / observe
# Screenshot, RapidOCR, numbered red boxes. Refs grow for the whole run and are never reused.

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
    png: bytes       # screenshot at the model's canvas size (crops come from this)
    drawn: bytes     # with numbered boxes (what the model sees)
    elements: tuple[Element, ...]
    url: str
    scale: float = 1.0   # canvas pixels -> page points (mouse)

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
    """The only screenshot path. The page is fixed (Q10), so this is normally 1:1; the rescale is
    only a safety net if a screenshot ever comes back at another pixel density."""
    img, points_w = decode(await page.screenshot()), await page_width()
    img, scale = to_canvas(img, points_w)
    elements = number(ocr(img))
    HANDOFF.look = Look(encode(img), draw_numbered(img, elements), elements, page.url, scale)
    return HANDOFF.look


def to_canvas(img: np.ndarray, points_w: int) -> tuple[np.ndarray, float]:
    """Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point scale."""
    cw, ch = CFG.viewport
    f = min(cw / img.shape[1], ch / img.shape[0])
    out = cv2.resize(img, (round(img.shape[1] * f), round(img.shape[0] * f)),
                     interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC)
    return out, points_w / out.shape[1]


async def page_width() -> int:
    """The window's width in mouse points (the browser's size, not the site's content)."""
    return int(await page.evaluate("window.innerWidth"))


def canvas() -> tuple[int, int]:
    """The size of the image the model is looking at right now."""
    if HANDOFF.look is None:
        return CFG.viewport
    h, w = decode(HANDOFF.look.png).shape[:2]
    return w, h


def to_page(point: tuple[int, int]) -> tuple[float, float]:
    s = HANDOFF.look.scale if HANDOFF.look else 1.0
    return point[0] * s, point[1] * s


def hide_secrets(text: str) -> str:
    for name, value in SECRETS.items():
        if value:
            text = text.replace(value, f"<{name}>")
    return text


def blocks(prefix: str, look: Look) -> list[dict]:
    listing = "\n".join(f"[{e.ref}] {hide_secrets(e.text)!r} box=({e.box.x1},{e.box.y1},{e.box.x2},{e.box.y2})"
                        for e in look.elements)
    return [{"type": "text", "text": f"{prefix}\nURL: {look.url}\nText on screen:\n{listing}"},
            {"type": "image", "base64": base64.b64encode(look.drawn).decode(),
             "mime_type": "image/png"}]


# %%
def element_at(look: Look, point: tuple[int, int]) -> Element | None:
    return next((e for e in look.elements if e.box.contains(*point)), None)


def label_near(look: Look, point: tuple[int, int], radius: int = 250,
               skip: Element | None = None, avoid: set[str] | None = None) -> Element | None:
    """The text above/left of the point that labels it. Never a value: it has a letter (not an
    account number or amount) and is nothing typed or entered this run. A label on the point's own
    row, to its left, wins (a wide form); else the nearest (a label above its box)."""
    px, py, avoid = *point, run_values() if avoid is None else avoid
    dist = lambda e: abs(e.box.center[0] - px) + abs(e.box.center[1] - py)  # noqa: E731
    near = [e for e in look.elements if e is not skip and re.search(r"[^\W\d_]", e.text)
            and norm(e.text) not in avoid and e.box.x1 <= px and e.box.y1 <= py and dist(e) <= radius]
    same_row = [e for e in near if e.box.y1 <= py <= e.box.y2 and e.box.x2 <= px]
    return min(same_row or near, key=dist, default=None)


def spot(look: Look, el: Element) -> dict:
    """Text, box, and ordinal (the Nth element on screen with the same text), for replay's rungs."""
    same = [e for e in look.elements if norm(e.text) == norm(el.text)]
    return {"text": el.text, "box": [el.box.x1, el.box.y1, el.box.x2, el.box.y2],
            "ordinal": same.index(el) + 1}


def where(look: Look, point: tuple[int, int], own: Element | None = None) -> dict:
    """R14: anchor label + offset (rung 2) and the clicked element (rung 1). The text under the
    point is never the anchor: in a box it could be a value."""
    label = label_near(look, point, skip=element_at(look, point))
    if label is None:
        return {"own": spot(look, own) if own else None}
    cx, cy = label.box.center
    return {"own": spot(look, own) if own else None, "anchor": spot(look, label),
            "label": label.text, "offset": [point[0] - cx, point[1] - cy]}


def crop_box(point: tuple[int, int], el: Element | None) -> Box:
    w, h = canvas()
    if el:
        p = CFG.crop_pad
        b = Box(el.box.x1 - p, el.box.y1 - p, el.box.x2 + p, el.box.y2 + p)
    else:
        cw, ch = CFG.point_crop
        b = Box(point[0] - cw // 2, point[1] - ch // 2, point[0] + cw // 2, point[1] + ch // 2)
    return Box(max(b.x1, 0), max(b.y1, 0), min(b.x2, w), min(b.y2, h))


def cut_crop(look: Look, point: tuple[int, int], keep: Element | None) -> bytes:
    """Crop around the target, with every other piece of text blanked out."""
    b = crop_box(point, keep)
    crop = decode(look.png)[b.y1:b.y2, b.x1:b.x2].copy()
    fill = np.median(crop.reshape(-1, 3), axis=0)
    for e in look.elements:
        if e is not keep and e.box.overlaps(b):
            crop[max(e.box.y1 - b.y1, 0):e.box.y2 - b.y1, max(e.box.x1 - b.x1, 0):e.box.x2 - b.x1] = fill
    return encode(crop)


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
# ## Safety & handoff
# When a human is called in and where they answer. The site tab ignores real input all run.

# %%
@dataclass
class HandoffState:
    goal: str = ""
    look: Look | None = None
    saved: dict[str, str] = field(default_factory=dict)
    declined: set[str] = field(default_factory=set)
    recent: list[str] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)     # the one event log
    login_tries: int = 0
    typed_secrets: set[str] = field(default_factory=set)
    typed_texts: set[str] = field(default_factory=set)
    login_blocked: bool = False
    stuck: str = ""
    entered: dict[str, str] = field(default_factory=dict)   # label -> value shown to the reviewer
    steps: int = 0
    fails: int = 0
    allow_send: bool = False       # set only around a login click
    given: list[str] = field(default_factory=list)   # what the human said: goal + every answer
    verdict: str = ""              # what the send gate decided during the last action
    takeover: list[dict] | None = None   # the human's pages and sends, only while they hold control
    dropdowns: list[dict] = field(default_factory=list)   # the page's dropdowns, read before each action
    redact: set[str] = field(default_factory=set)   # run values, kept only to mask evidence (in memory)
    answer: str = ""               # the agent's final message
    messages: list = field(default_factory=list)   # the run's chat, for the evidence transcript
    final_shot: bytes | None = None   # the page when a run ends STUCK/DECLINED or crashes


HANDOFF = HandoffState()
DECLINED = "DECLINED by a human. Do not retry or work around it. Reply 'DECLINED: <why>' and stop."


def norm(text: str | None) -> str:
    return " ".join((text or "").casefold().split()).rstrip(".:!?").strip()


def run_values() -> set[str]:
    """Every value typed, entered or given this run, plus the secrets (in memory only)."""
    return {norm(v) for v in (*HANDOFF.typed_texts, *HANDOFF.given, *HANDOFF.entered.values(),
                              *SECRETS.values()) if norm(v) and v != "******"}


def flag_leaks(log: list[dict], values: set[str]) -> None:
    """Mark (never store) an event whose label, anchor or own text is one of this run's values,
    so the save refuses it. Run before the values are dropped."""
    for ev in log:
        texts = (ev.get("label"), (ev.get("anchor") or {}).get("text"), (ev.get("own") or {}).get("text"),
                 ev["args"].get("hint"))
        if any(norm(t) in values for t in texts if t):
            ev["leak"] = True


def current_page() -> str:
    return urlparse(page.url).path.split(";")[0].rstrip("/").rsplit("/", 1)[-1].lower()


def is_sensitive(label: str) -> bool:
    return any(w in label.casefold() for w in CFG.sensitive_words)


def log(tool: str, args: dict, result: str, point=None, crop: bytes | None = None, **extra) -> None:
    HANDOFF.log.append({"tool": tool, "args": args, "result": result.split("\n")[0],
                        "point": point, "url": page.url, "crop": crop, **extra})


def needs_human_value(value: str, label: str) -> bool:
    """D34: a sensitive field, or a value the user never gave, is typed by a human."""
    return not norm(value) or is_sensitive(label) or norm(value) not in norm(HANDOFF.goal)


def mark_stuck(reason: str) -> str:
    HANDOFF.stuck = reason
    return f"STUCK: {reason}"


async def human_help(title: str, reason: str) -> str:
    """Q21, open-ended: the human answers in words, takes over the site, or stops the run."""
    choice = await CONTROL.ask(title, reason, "help",
                               image=HANDOFF.look.drawn if HANDOFF.look else None) or "stop"
    if choice.startswith("say:") and choice[4:].strip():
        log("ask_human", {"reason": reason}, "answered")
        HANDOFF.given.append(choice[4:].strip())
        result = f"The human says: {choice[4:].strip()}"
    elif choice == "takeover":
        if stuck := await take_over(reason):
            return mark_stuck(stuck) + ". Reply 'STUCK: ' with it and stop."
        result = "A human took over the site and handed back. Call observe and continue the task."
    else:
        log("stuck", {"reason": reason}, "human stopped the run")
        return f"STOPPED by the human: {reason}. Reply 'STUCK: {reason}' and stop."
    HANDOFF.stuck, HANDOFF.recent, HANDOFF.fails, HANDOFF.steps = "", [], 0, 0
    HANDOFF.login_blocked, HANDOFF.login_tries = False, 0
    return result


async def snap() -> bytes | None:
    """An evidence screenshot: short timeout, None on failure. A page whose navigation is held by
    guard_send never finishes a screenshot, so evidence must never be able to hang or crash a run."""
    try:
        return await page.screenshot(timeout=CFG.snap_ms, animations="disabled")
    except PlaywrightError:
        return None


async def take_over(reason: str) -> str | None:
    """Q21: the one time the site unlocks for a human. What they did is kept as EVIDENCE, never as
    steps (recordable: false, so the save refuses): each page they land on (path only) and each
    send (path only, via guard_send), plus a screenshot at the start and at hand-back. The
    screenshots may show values: in memory only, redact before persisting (Q16). Returns a STUCK
    reason if a send the human started is still held long after Done, else None."""
    started, url_before, actions = time.monotonic(), page.url, []
    shot_before = await snap()

    def on_page(frame) -> None:
        if frame == page.main_frame:
            actions.append({"kind": "page", "path": urlparse(frame.url).path})

    HANDOFF.takeover, HANDOFF.dropdowns, stuck = actions, [], None
    page.on("framenavigated", on_page)
    await ext_call("setMode('YOU')")
    watchers = [asyncio.create_task(watch_button())]
    try:
        async with LOCK.open():      # the human's own sends still go through both gates
            await CONTROL.ask("You are in control", f"{reason} Work in the site tab. When you're "
                              "done, click the Agent hand-back icon in the browser toolbar (pin it "
                              "once from the puzzle-piece menu), or Done in the Agent control tab. "
                              "If you log in with a new user, the agent carries on from there.",
                              "takeover", who="human")
        try:     # a send the human started is still held: its gate is on screen next; wait for it
            await asyncio.wait_for(SEND_GATE.acquire(), CFG.handback_s)
            SEND_GATE.release()
        except asyncio.TimeoutError:
            stuck = f"a send the human started was still held {CFG.handback_s}s after Done"
    finally:
        for task in watchers:    # the button watcher is never worth failing a hand-back
            task.cancel()
        await asyncio.gather(*watchers, return_exceptions=True)
        await ext_call("setMode('AI')")
        page.remove_listener("framenavigated", on_page)
        HANDOFF.takeover = None
    shot_after = await snap()
    HANDOFF.typed_secrets = set()
    if not host_allowed(page.url):
        await page.goto(BASE_URL)
    log("take_over", {"reason": reason}, "handed back", url_before=urlparse(url_before).path,
        seconds=round(time.monotonic() - started), human_entry=True, recordable=False,
        actions=actions, shot_before=shot_before, shot_after=shot_after)
    return stuck


async def ext_call(script: str) -> object:
    """Q16: one bounded call into the hand-back extension's service worker, never the site page.
    No extension, or one that errors or hangs, gives None: the take-over carries on without it."""
    if EXT is None:
        return None
    try:
        return await asyncio.wait_for(EXT.evaluate(script), CFG.ext_s)
    except (PlaywrightError, asyncio.TimeoutError):
        return None


async def watch_button() -> None:
    """Hands back once the toolbar button's click count rises above where it was at the start."""
    base = await ext_call("self.handbackClicked || 0")
    while True:
        await asyncio.sleep(CFG.ext_poll_s)
        n = await ext_call("self.handbackClicked || 0")
        if base is None:
            base = n
        elif n is not None and n > base:
            CONTROL.answer("takeover", "done")
            return


async def offer_control(msg: str) -> str:
    """Only the reason: the first line of the tool result, without its prefix or instructions."""
    reason = msg.splitlines()[0].split(":", 1)[-1].strip().split(". Reply")[0]
    return await human_help("The agent is stuck", reason[:200])


def note_call(tool: str, args: dict) -> str | None:
    """The same call N times in a row means STUCK."""
    key = f"{tool}:{json.dumps(args, sort_keys=True, default=str)}"
    HANDOFF.recent = [*HANDOFF.recent, key][-CFG.repeat_limit:]
    if len(HANDOFF.recent) == CFG.repeat_limit and len(set(HANDOFF.recent)) == 1:
        return mark_stuck(f"repeated {tool} {CFG.repeat_limit} times")
    return None


def after_login_click(screen_text: str) -> str | None:
    """D69: at most N login tries; a failure text on screen stops login for the run."""
    HANDOFF.login_tries += 1
    failed = next((t for t in CFG.login_failure_texts if t in screen_text.casefold()), None)
    if failed or HANDOFF.login_tries >= CFG.login_limit:
        HANDOFF.login_blocked = True
    return f"STOP: login failed ('{failed}'). Do not try again. Reply 'STUCK: <why>'." if failed else None


async def gate_click(text: str | None, image: bytes | None = None) -> str | None:
    """D33: None means go ahead; otherwise the refusal the tool returns. No per-click approval."""
    name = norm(text)
    if name and any(re.search(rf"\b{re.escape(w)}\b", name) for w in CFG.deny_words):
        return f"REFUSED: '{text}' is not allowed. Find another way or reply 'STUCK: <why>'."
    if name in HANDOFF.declined:
        return "DECLINED earlier by a human. Do not retry. Reply 'DECLINED: <why>' and stop."
    if name in CFG.login_words and HANDOFF.login_blocked:
        return "BLOCKED: login hit its limit. Do not try again. Reply 'STUCK: <why>'."
    if name in CFG.login_words and (missing := sorted(set(SECRETS) - HANDOFF.typed_secrets)):
        return f"NOT YET: type {missing} with type_secret first, one box each, then click this."
    return None    # moving around needs no approval; anything that sends data meets the two gates


SEND_GATE = asyncio.Lock()


DROPDOWNS_JS = """() => [...document.querySelectorAll('select')].map(s => {
  const r = s.getBoundingClientRect();
  return {value: s.value, text: s.options[s.selectedIndex]?.text.trim() ?? '',
          options: [...s.options].map(o => o.text.trim()),
          at: r.width && r.height ? [r.left + r.width / 2, r.top + r.height / 2] : null};
})"""


async def read_dropdowns() -> list[dict]:
    """The page's dropdowns, read BEFORE an action (never while guard_send holds a request: then a
    page read never returns). Bounded: empty on a timeout or error."""
    try:
        return await asyncio.wait_for(page.evaluate(DROPDOWNS_JS), CFG.snap_ms / 1000)
    except (asyncio.TimeoutError, PlaywrightError):
        return []


async def log_sent_dropdowns(look: Look, sent: dict[str, str]) -> None:
    """A dropdown whose value this send carries is a step, even one left on its default or set in
    a gate form: replay must choose it, never inherit the page's default. Logged before the send
    click, with its label and position only. The value is never logged, and the crop blanks it."""
    values = {v for v in sent.values() if v}
    for d in HANDOFF.dropdowns:            # read before the click: the page is not touched here
        if d["at"] and values & {d["value"], d["text"]}:
            point = (round(d["at"][0] / look.scale), round(d["at"][1] / look.scale))
            spots = where(look, point)
            log("select_option", {"hint": spots.get("label") or "option"}, "sent dropdown", point,
                cut_crop(look, point, None), dropdown=True, **spots)


async def dropdown_options(fields: dict[str, str], keys: list[str]) -> list[list[str]]:
    """For each key: the options of the page dropdown whose CURRENT value is exactly this value,
    else [] (a plain box). Each dropdown is used once, so '1' in five fields never grabs one twice.
    From the pre-action read: guard_send never touches the page while it holds a request."""
    free = list(HANDOFF.dropdowns)
    out = []
    for k in keys:
        hit = next((d for d in free if fields[k] and fields[k] in (d["value"], d["text"])), None)
        if hit:
            free.remove(hit)
        out.append([hide_secrets(o) for o in hit["options"]] if hit and len(hit["options"]) > 1 else [])
    return out


def mismatches(sent: dict[str, str]) -> list[str]:
    """Numbers being sent that the human never gave (goal or answers), e.g. account 1450 vs 1400.
    Only digit groups are compared: they are what a wrong transfer is made of, on any site."""
    given = set(re.findall(r"\d+(?:\.\d+)?", " ".join([HANDOFF.goal, *HANDOFF.given])))
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
    """Every value a request sends, from its query, a form body, or a JSON body (nested keys dotted)."""
    data = _json(req.post_data)
    body = _flat(data) if data is not None else dict(parse_qsl(req.post_data or ""))
    return dict(parse_qsl(urlparse(req.url).query)) | body


def rebuilt(req, fields: dict[str, str]) -> tuple[str, str | None]:
    """The request's url and body with these values put back in, in the same format."""
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
    """'address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)."""
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key.replace(".", " ").replace("_", " ")).split()
    return " ".join(words).capitalize()


async def guard_send(route) -> None:
    """Every request that sends data (not GET) is held for two human gates, however it was
    triggered: a click, Enter, or the page's own script. Generic: no button names needed."""
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or HANDOFF.allow_send:
        return await route.continue_()
    async with SEND_GATE:
        # Nothing in here touches the page (no evaluate, screenshot or locator): while this request
        # is held, a form POST (a navigation) keeps any page call from ever returning.
        human = HANDOFF.takeover is not None      # the human's own send during a take-over
        fields = sent_fields(req)
        original = dict(fields)
        if not human and (bad := mismatches(fields)):   # a human's own values: nothing to compare
            # e.g. a dropdown left on its default: the human never gave that value. Ask them now,
            # with the page's value filled in, and send what they confirm. The send is only held.
            opts = await dropdown_options(fields, bad)
            fixed = await CONTROL.form("You never gave these. Check or correct them:",
                                       [(pretty(k), False) for k in bad], [fields[k] for k in bad], opts)
            if not fixed or not all(fixed):
                HANDOFF.verdict = f"STUCK: No value confirmed for {', '.join(bad)}. Nothing was sent."
                return await route.abort()
            fields.update(zip(bad, fixed))
            HANDOFF.given.extend(fixed)
        # The last look is the page as filled (the agent's own send); a human's send during a
        # take-over has none that is current, so no image.
        look = None if human else HANDOFF.look
        shot = look.png if look else None  # dropped once values are edited
        while True:     # Gate 1: Approve, or Edit = back to the form with every value, then again
            sent = hide_secrets("\n".join(f"{pretty(k)}: {'******' if is_sensitive(k) else v}"
                                           for k, v in fields.items())[:1200])
            what = f"Sending to {urlparse(req.url).path}:\n{sent or '(no fields)'}"
            choice = await CONTROL.ask("Gate 1 of 2: confirm the details", what, "confirm",
                                       image=shot if fields == original else None)
            if choice == "approve":
                break
            if choice != "edit":             # control tab closed: fail closed
                HANDOFF.verdict = "STUCK: the details were not confirmed. Nothing was sent."
                return await route.abort()
            editable = [k for k in fields if not is_sensitive(k)]
            opts = [[] for _ in editable] if human else await dropdown_options(fields, editable)
            new = await CONTROL.form("Edit the details, then Submit:",
                                     [(pretty(k), False) for k in editable],
                                     [fields[k] for k in editable], opts)
            if new:
                fields.update(zip(editable, new))
                HANDOFF.given.extend(v for v in new if v)
        url, body = rebuilt(req, fields) if fields != original else (req.url, req.post_data)
        if await CONTROL.ask("Gate 2 of 2: confirm sending", f"{what}\nThis cannot be undone.",
                             "approve", image=shot if fields == original else None) != "approve":
            HANDOFF.verdict = DECLINED
            return await route.abort()
        if look:                                   # the page's dropdowns hold what was on screen
            await log_sent_dropdowns(look, original)
        HANDOFF.redact |= {v for v in fields.values() if v}    # e.g. a human's $100000: masked in evidence
        HANDOFF.entered = {}
        HANDOFF.verdict = "SENT: a human approved both gates."
        log("send", {"path": urlparse(req.url).path}, "approved by human",
            corrected=[k for k in fields if fields[k] != original[k]])
        if human and HANDOFF.takeover is not None:
            HANDOFF.takeover.append({"kind": "send", "path": urlparse(req.url).path})
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
    "text": "<textarea id=v rows=3 cols=60></textarea><button onclick=\"cuaReply(v.value)\">Send</button>",
    "takeover": "<button onclick=\"cuaReply('done')\">Done, hand back to agent</button>",
    "help": "<textarea id=v rows=4 cols=60 placeholder='Tell the agent what to do'></textarea><br>"
            "<button onclick=\"cuaReply('say:' + v.value)\">Send answer</button>"
            "<button onclick=\"cuaReply('takeover')\">Take over the site</button>"
            "<button onclick=\"cuaReply('stop')\">Stop the run</button>",
    "form": "<button onclick=\"cuaReply(JSON.stringify([...document.querySelectorAll('.f')]"
            ".map(e => e.value)))\">Submit</button><button onclick=\"cuaReply('')\">Skip</button>",
    "status": "",
}


class ControlWindow:
    """Our own page: the only place a human answers. Closing it fails closed (None)."""

    def __init__(self, win: object) -> None:
        self.win = win
        self._stack: list[tuple[asyncio.Future, tuple]] = []   # newest question on top

    def on_reply(self, value: str | None) -> None:
        """Answers the question on top. Closing the window (None) answers every one: fail closed."""
        for fut, _ in (self._stack if value is None else self._stack[-1:]):
            if not fut.done():
                fut.set_result(value)

    def answer(self, mode: str, value: str) -> None:
        """Answers the newest open question of this mode, wherever it sits on the stack."""
        for fut, q in reversed(self._stack):
            if q[2] == mode and not fut.done():
                fut.set_result(value)
                return

    async def show(self, title: str, details: str = "", mode: str = "status",
                   image: bytes | None = None, who: str = "agent", rows: str = "") -> None:
        tab = "Agent control" if mode == "status" else "\u25b6 Agent control: your turn"
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

    async def ask(self, title: str, details: str, mode: str, image: bytes | None = None,
                  who: str = "agent", rows: str = "") -> str | None:
        """A new question supersedes the one on screen (e.g. a gate during a take-over); when it is
        answered, the earlier one comes back exactly as it was."""
        entry = (asyncio.get_running_loop().create_future(), (title, details, mode, image, who, rows))
        self._stack.append(entry)
        try:
            await self._front(entry[1])
            return await entry[0]
        finally:
            self._stack.remove(entry)
            if self.win.is_closed():
                pass
            elif self._stack:
                await self._front(self._stack[-1][1])
            else:
                await self.show("Agent is working")
                await page.bring_to_front()

    async def _front(self, q: tuple) -> None:
        await self.show(*q)
        await (page if q[2] == "takeover" else self.win).bring_to_front()

    async def form(self, title: str, fields: list[tuple[str, bool]], values: list[str] | None = None,
                   options: list[list[str]] | None = None) -> list[str] | None:
        """One labelled input per field (label, masked), optionally prefilled. A dropdown row shows
        all its options and suggests them as you type. None if skipped or the window closed."""
        n = len(fields)
        rows = "".join(_row(i, label, masked, value, opts) for i, ((label, masked), value, opts)
                       in enumerate(zip(fields, values or [""] * n, options or [[]] * n)))
        answer = await self.ask(title, "Our code enters these into the site. The agent never "
                                "sees them.", "form",
                                rows=rows)
        return json.loads(answer) if answer else None


def _row(i: int, label: str, masked: bool, value: str, opts: list[str]) -> str:
    """A dropdown becomes a real <select> of its options; anything else a text/password box."""
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


async def wait_for_change(before: bytes) -> None:
    """The response to a send lands after the human's approval, not after the click: wait until
    the page differs from before the click and has stopped changing (bounded)."""
    end, last = time.monotonic() + CFG.send_wait_ms / 1000, before
    while time.monotonic() < end:
        await page.wait_for_timeout(CFG.settle_ms)
        shot = await page.screenshot()
        if not screens_same(before, shot) and screens_same(last, shot):
            return
        last = shot


async def act(*steps) -> Look:
    """Unlock the site tab, run our own input steps, relock, settle, take a new look."""
    before = await page.screenshot()
    HANDOFF.dropdowns = await read_dropdowns()     # what a send from this action will need
    async with LOCK.open():
        for step in steps:
            await step()
    await page.wait_for_timeout(CFG.settle_ms)
    async with SEND_GATE:      # a send held for the human finishes first
        pass
    if HANDOFF.verdict.startswith("SENT"):
        await wait_for_change(before)
    return await take_look()


def into_box(point: tuple[int, int], value: str) -> tuple:
    """Click the box, clear what is in it, type. Retries replace instead of doubling up."""
    return (lambda: page.mouse.click(*to_page(point)), lambda: page.keyboard.press("ControlOrMeta+A"),
            lambda: page.keyboard.press("Backspace"), lambda: page.keyboard.type(value))


# D-B (user choice, 2026-09-29): the ONE non-visual exception. A native dropdown's list is drawn
# by the OS (macOS) outside the page, so no screenshot shows it and no key moves it. For the
# <select> under a point only, we read its options and set it by value. Everything else stays visual.
SELECT_AT_JS = """([x, y, want]) => {
  let el = document.elementFromPoint(x, y)?.closest('select');
  if (!el) {            // pointed at its label: take the nearest dropdown within 250px
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
  const i = opts.findIndex(t => t.toLowerCase().includes(want.toLowerCase()));
  if (i < 0) return false;
  el.selectedIndex = i;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2];
}"""


async def list_options(point: tuple[int, int], label: str = "") -> list[str]:
    """Every option of the dropdown at this point ([] if it is not a dropdown)."""
    return [hide_secrets(o) for o in (await page.evaluate(SELECT_AT_JS, [*to_page(point), None]) or [])]


async def choose_option(point: tuple[int, int], option: str, label: str = "") -> bool:
    """Select the first option containing this text in the dropdown at (or next to) this point;
    OCR of the dropdown's own box confirms it."""
    at = await page.evaluate(SELECT_AT_JS, [*to_page(point), option])
    if not isinstance(at, list):
        return False
    await page.wait_for_timeout(CFG.settle_ms)
    look = await take_look()
    return norm(option) in norm(read_near(look, (round(at[0] / look.scale), round(at[1] / look.scale))))


async def human_fills(fields: list[tuple[tuple[int, int], str]], dropdown: bool = False,
                      dropdowns: list[bool] | None = None) -> str:
    """Q16/D34/D55: the human answers in the control window's form; our code enters every value.
    The site stays locked throughout. Values are never logged and never reach the model."""
    look, hints = HANDOFF.look, ", ".join(h for _, h in fields)
    flags = dropdowns or [dropdown] * len(fields)
    options = [await list_options(p, h) if f or element_at(look, p) else [] for (p, h), f in zip(fields, flags)]
    kinds = [f or len(o) > 1 for f, o in zip(flags, options)]      # a list that moves = a dropdown
    options = [o if k else [] for o, k in zip(options, kinds)]
    answers = await CONTROL.form(f"Please fill in: {hints}",
                                 [(h, is_sensitive(h)) for _, h in fields], options=options)
    if not answers or not any(answers):
        return f"SKIPPED: the human gave no values for {hints}."
    failed = []
    for (point, hint), value, is_dropdown in zip(fields, answers, kinds):
        if not value:
            continue
        if is_dropdown:
            if not await choose_option(point, value, hint):
                failed.append(hint)
                continue
        else:
            await act(*into_box(point, value))
        HANDOFF.entered[hint] = "******" if is_sensitive(hint) else value
        if not is_sensitive(hint):
            HANDOFF.given.append(value)
        log("request_value", {"hint": hint}, "human entry", point,
            cut_crop(look, point, element_at(look, point) if is_dropdown else None),
            human_entry=True, dropdown=is_dropdown, **where(look, point))
    if failed:
        return mark_stuck(f"not in the list: {', '.join(failed)}")
    return f"A human gave: {hints}. Our code entered them. Do not type them again. Continue."


# %%
LOCK = SiteLock(await page.context.new_cdp_session(page))
await LOCK.set(True)
await page.unroute("**/*")
await page.route("**/*", guard_send)
CONTROL = ControlWindow(control_page)
await control_page.expose_function("cuaReply", CONTROL.on_reply)
control_page.on("close", lambda _: CONTROL.on_reply(None))
await CONTROL.show("Agent is working")
await page.bring_to_front()
print("site locked | control window open")

# %% [markdown]
# ## Tools
# One call at a time. Every input goes through `act`; every click through `gate_click`.

# %%
ACT_LOCK = asyncio.Lock()
FAILED = ("NO CHANGE", "NOTHING TYPED", "TYPED at", "STALE", "OUT OF VIEW", "REFUSED", "NOT YET",
          "LOOK FIRST", "BAD TARGET", "SKIP")   # tool results that mean "that did not work"


def one_at_a_time(fn):
    @functools.wraps(fn)
    async def wrapper(*a, **k):
        async with ACT_LOCK:
            HANDOFF.steps += 1
            over = HANDOFF.steps > CFG.step_budget and mark_stuck(f"{CFG.step_budget} steps without finishing")
            HANDOFF.verdict = ""
            result = over or note_call(fn.__name__, k) or await fn(*a, **k)
            if HANDOFF.verdict.startswith(("STUCK", "DECLINED")):
                return await offer_control(HANDOFF.verdict) if HANDOFF.verdict.startswith("STUCK") \
                    else HANDOFF.verdict
            head = result if isinstance(result, str) else result[0]["text"]
            if head.startswith(("STUCK:", "STOP:", "BLOCKED:")):
                return await offer_control(head)
            HANDOFF.fails = HANDOFF.fails + 1 if head.startswith(FAILED) else 0
            if HANDOFF.verdict.startswith("SENT") and not isinstance(result, str):
                result[0]["text"] = f"{HANDOFF.verdict} {head}"
            if HANDOFF.fails >= CFG.unsure_limit:
                return await human_help("The agent is unsure", f"{HANDOFF.fails} tries failed. "
                                        f"Last: {head.splitlines()[0][:120]}")
            return result

    return wrapper


def resolve_point(ref: int | None, x: int | None, y: int | None) -> tuple[int, int] | str:
    look = HANDOFF.look
    if look is None:
        return "LOOK FIRST: call observe."
    if (ref is None) == (x is None or y is None):
        return "BAD TARGET: give either ref, or both x and y."
    if ref is not None:
        el = look.get(ref)
        return el.box.center if el else f"STALE: [{ref}] is not in the latest look. Call observe."
    w, h = canvas()
    return (x, y) if 0 <= x < w and 0 <= y < h else f"OUT OF VIEW: ({x},{y}) is outside {w}x{h}."


async def reply(msg: str) -> list:
    return blocks(msg, HANDOFF.look or await take_look())


@tool(parse_docstring=True)
@one_at_a_time
async def observe() -> list:
    """Take a new screenshot and number every piece of text on it. Old numbers stop working."""
    return blocks("Current page.", await take_look())


def landed(before: Look, after: Look) -> list[str]:
    """Text the page showed in response to a send: the replay checkpoint. Fixed page text only:
    nothing with a digit (amounts, account numbers) and nothing the human or the goal gave."""
    old, given = norm(before.text), [norm(v) for v in (*HANDOFF.given, *HANDOFF.typed_texts) if norm(v)]
    return [e.text for e in after.elements if norm(e.text) and norm(e.text) not in old
            and re.search(r"[^\W\d_]", e.text) and not re.search(r"\d", e.text)
            and not any(v in norm(e.text) for v in given)]


@tool(parse_docstring=True)
@one_at_a_time
async def click(ref: int | None = None, x: int | None = None, y: int | None = None) -> list:
    """Click a numbered box, or a spot with no number by x,y. Risky clicks ask a human first.

    Args:
        ref: Number of the box in the latest look.
        x: Pixel x of a spot with no number.
        y: Pixel y of a spot with no number.
    """
    point = resolve_point(ref, x, y)
    if isinstance(point, str):
        return await reply(point)
    before = HANDOFF.look
    el = element_at(before, point)
    text, crop, args = (el.text if el else None), cut_crop(before, point, el), {"ref": ref, "x": x, "y": y}
    if text and any(norm(v) and norm(v) in norm(text) for v in (*SECRETS.values(), *HANDOFF.typed_texts)):
        msg = "REFUSED: that number is text inside a box you already filled. It is done; move on."
        log("click", args, msg, point, crop)
        return blocks(msg, before)
    spots = where(before, point, own=el)
    if refusal := await gate_click(text, crop):
        log("click", args, refusal, point, crop, text=text, **spots)
        return blocks(refusal, before)
    HANDOFF.allow_send = norm(text) in CFG.login_words
    try:
        after = await act(lambda: page.mouse.click(*to_page(point)))
    finally:
        HANDOFF.allow_send = False
    msg, sent = f"Clicked {text or point!r}.", HANDOFF.verdict.startswith("SENT")
    if page.url != before.url:
        HANDOFF.entered = {}
    if not host_allowed(page.url):
        await page.go_back()
        after, msg = await take_look(), "BLOCKED: left the allowed site. Went back."
    elif screens_same(before.png, after.png) and not sent:      # a send that went out is a real step
        msg = f"NO CHANGE after clicking {point}. Look again and retry."
    if norm(text) in CFG.login_words:
        HANDOFF.typed_secrets.clear()
        msg = after_login_click(after.text) or msg
    log("click", args, msg, point, crop, text=text, **spots, **({"landed": landed(before, after)} if sent else {}))
    return blocks(msg, after)


@tool(parse_docstring=True)
@one_at_a_time
async def type_text(text: str, ref: int | None = None, x: int | None = None,
                    y: int | None = None) -> list:
    """Click a box (by number or x,y) and type text. Only values from the user's goal.

    Args:
        text: The text to type. It must come from the goal.
        ref: Number of a box, or leave empty and give x and y.
        x: Pixel x of an empty input box.
        y: Pixel y of an empty input box.
    """
    point = resolve_point(ref, x, y)
    if isinstance(point, str):
        return await reply(point)
    label = label_near(HANDOFF.look, point)
    hint = label.text if label else "value"
    if needs_human_value(text, hint):
        return await reply(await human_fills([(point, hint)]))
    crop, spots = cut_crop(HANDOFF.look, point, None), where(HANDOFF.look, point)
    after = await act(*into_box(point, text))
    HANDOFF.typed_texts.add(text)
    shown = read_near(after, point)
    msg = (f"Typed at {point}. Box shows {shown!r}." if norm(text) in norm(shown)
           else f"TYPED at {point} but the box shows {shown!r}. Look again.")
    HANDOFF.entered[hint] = text
    log("type_text", {"ref": ref, "x": x, "y": y}, msg.split(" Box shows")[0], point, crop,
        **spots)
    return blocks(msg, after)


@tool(parse_docstring=True)
@one_at_a_time
async def type_secret(name: str, ref: int | None = None, x: int | None = None,
                      y: int | None = None) -> list | str:
    """Click a box and type a stored secret. You give only its name and never see the value.

    Args:
        name: The secret's name.
        ref: Number of a box, or leave empty and give x and y.
        x: Pixel x of an empty input box.
        y: Pixel y of an empty input box.
    """
    if not SECRETS.get(name):
        return await reply(f"UNKNOWN SECRET '{name}'. Use one of: {sorted(SECRETS)}")
    if not host_allowed(page.url):
        return await reply("REFUSED: this site is not on the allowlist.")
    point = resolve_point(ref, x, y)
    if isinstance(point, str):
        return await reply(point)
    before = HANDOFF.look
    crop, spots = cut_crop(before, point, None), where(before, point)
    after = await act(*into_box(point, SECRETS[name]))
    if is_sensitive(name) and SECRETS[name] in read_near(after, point):
        HANDOFF.look = None
        log("type_secret", {"secret_name": name}, "STOP: secret visible", point, crop, **spots)
        return "STOP: the box shows the secret as plain text. Call ask_human; do not observe."
    if typed := spot_changed(before, after, point):
        HANDOFF.typed_secrets.add(name)
    msg = (f"Typed secret '{name}' at {point}." if typed
           else f"NOTHING TYPED at {point}: that point is not an input box. Point at the empty "
                "box itself (usually right of or below its label) and try once more.")
    log("type_secret", {"secret_name": name}, msg, point, crop, **spots)
    return blocks(msg, after)


@tool(parse_docstring=True)
@one_at_a_time
async def select_option(option: str, ref: int | None = None, x: int | None = None,
                        y: int | None = None) -> list:
    """Pick the dropdown option that matches. Nothing is typed. Give option="" if the goal does not name it.

    Args:
        option: Visible option text from the goal, or "" to let a human choose.
        ref: Number of the dropdown, or leave empty and give x and y.
        x: Pixel x of the dropdown.
        y: Pixel y of the dropdown.
    """
    point = resolve_point(ref, x, y)
    if isinstance(point, str):
        return await reply(point)
    label = label_near(HANDOFF.look, point)
    hint = label.text if label else "option"
    if needs_human_value(option, hint):
        return await reply(await human_fills([(point, hint)], dropdown=True))
    own = element_at(HANDOFF.look, point)
    crop, spots = cut_crop(HANDOFF.look, point, own), where(HANDOFF.look, point)
    if not await choose_option(point, option, hint):
        return await reply(mark_stuck(f"'{option}' is not an option in '{hint}'"))
    msg = f"Selected '{option}' at {point}."
    HANDOFF.entered[hint] = option
    log("select_option", {"ref": ref, "x": x, "y": y}, "Selected.", point, crop, **spots)
    return await reply(msg)


@tool(parse_docstring=True)
@one_at_a_time
async def scroll(direction: str, x: int | None = None, y: int | None = None) -> list:
    """Scroll up or down, then take a new look. Old numbers stop working.

    Args:
        direction: 'up' or 'down'.
        x: Optional pixel x inside a small scrolling panel.
        y: Optional pixel y inside a small scrolling panel.
    """
    before = HANDOFF.look or await take_look()
    w, h = canvas()
    at = (x, y) if x is not None and y is not None else (w // 2, h // 2)
    dy = CFG.scroll_px if direction == "down" else -CFG.scroll_px
    after = await act(lambda: page.mouse.move(*to_page(at)), lambda: page.mouse.wheel(0, dy))
    msg = f"Scrolled {direction}."
    if screens_same(before.png, after.png):
        msg = "BOTTOM OF PAGE reached." if dy > 0 else "TOP OF PAGE reached."
    log("scroll", {"direction": direction, "x": x, "y": y}, msg)
    return blocks(msg, after)


@tool(parse_docstring=True)
@one_at_a_time
async def open_path(path: str) -> list:
    """Open a page on the allowed site by its path (a menu link or a sitemap path).

    Args:
        path: A path you SAW on this site (a link's target or the current URL). Never guess one.
    """
    url = urljoin(BASE_URL + "/", path.lstrip("/"))
    refusal = None
    if not host_allowed(url):
        refusal = "REFUSED: that host is not allowed."
    elif any(w in norm(path) for w in CFG.deny_words):
        refusal = f"REFUSED: '{path}' is not allowed."
    elif any(norm(v) not in norm(HANDOFF.goal) for _, v in parse_qsl(urlparse(url).query)):
        refusal = "REFUSED: query values must come from the goal."
    log("open_path", {"path": path}, refusal or f"Opened {path}.")
    if refusal:
        return await reply(refusal)
    await page.goto(url)
    return blocks(f"Opened {path}.", await take_look())


def table_cell(look: Look, el: Element) -> dict | None:
    """Row key + column header for a value in a table, if it clearly sits in one."""
    row = [e for e in look.elements if e.box.y1 < el.box.y2 and el.box.y1 < e.box.y2]
    above = [e for e in look.elements
             if e.box.y2 <= el.box.y1 and e.box.x1 < el.box.x2 and el.box.x1 < e.box.x2]
    if not above or len(row) < 2:
        return None
    header, key = min(above, key=lambda e: e.box.y1), min(row, key=lambda e: e.box.x1)
    spans = sum(1 for e in row if header.box.x1 < e.box.x2 and e.box.x1 < header.box.x2)
    return None if key is el or spans > 1 else {"row_key": key.text, "column": header.text}


@tool(parse_docstring=True)
@one_at_a_time
async def extract_value(ref: int, save_as: str, value_type: str, description: str) -> str:
    """Save a value the goal asked for, read from a numbered box.

    Args:
        ref: Number of the box holding the value, not its header.
        save_as: Name to save it under, e.g. 'savings_balance'.
        value_type: Expected type, e.g. 'currency' or 'string'.
        description: What the value is, in plain words.
    """
    look = HANDOFF.look
    el = look.get(ref) if look else None
    if el is None:
        return f"STALE: [{ref}] is not in the latest look. Call observe."
    if not value_matches_type(el.text, value_type):
        return f"REFUSED: {el.text!r} is not a {value_type}. Pick the value box, not a header."
    HANDOFF.saved[save_as] = el.text
    args = {"ref": ref, "save_as": save_as, "value_type": value_type, "description": description}
    log("extract_value", args, "saved", el.box.center, cut_crop(look, el.box.center, el),
        table=table_cell(look, el), **where(look, el.box.center))
    return f"Saved {save_as} = {el.text!r}."


@tool(parse_docstring=True)
@one_at_a_time
async def finish_business_outcome(outcome: str, proof_text: str) -> str:
    """Report the business result, with text on the screen that proves it.

    Args:
        outcome: The result in plain words.
        proof_text: Exact text visible on the screen that proves it.
    """
    if norm(proof_text) not in norm(HANDOFF.look.text if HANDOFF.look else ""):
        return "REFUSED: that proof text is not on the screen. Observe and copy it exactly."
    log("finish_business_outcome", {"outcome": outcome, "proof_text": proof_text}, "OK")
    return "OK"


# %%
def start_page_refusal() -> str | None:
    """D34, generic: asking for form values on the page the run began on is too early."""
    if urlparse(page.url).path.split(";")[0] == urlparse(START_URL).path:
        return "NOT YET: you are on the start page. Open the page where the task is done first."
    return None


@tool(parse_docstring=True)
@one_at_a_time
async def request_missing_values(fields: list[dict[str, int | str]]) -> list:
    """Hand a human every field on this page the goal gives no value for (boxes and dropdowns).

    Args:
        fields: One entry per field: {"x": int, "y": int, "hint": "label you read",
            "dropdown": true if it is a dropdown (a box with a small arrow)}. For a dropdown,
            give x,y of the box itself, not its label.
    """
    if refusal := start_page_refusal():
        return await reply(refusal)
    points = [(resolve_point(None, int(f["x"]), int(f["y"])), str(f["hint"])) for f in fields]
    if bad := next((p for p, _ in points if isinstance(p, str)), None):
        return await reply(bad)
    flags = [bool(f.get("dropdown")) for f in fields]
    return await reply(await human_fills(points, dropdowns=flags) if points else "No fields given.")


@tool(parse_docstring=True)
@one_at_a_time
async def ask_human(question: str) -> str:
    """Ask a human whenever you are unsure: what to do, which option, what the goal means.

    Args:
        question: What you are unsure about, and what you see.
    """
    return await human_help("The agent asks", question)


TOOLS = [observe, click, type_text, type_secret, select_option, scroll, open_path, extract_value,
         finish_business_outcome, request_missing_values, ask_human]

# %% [markdown]
# ## Agent
# The system prompt and the deep agent, with a checkpointer so a run can be resumed.

# %%
VISUAL_SYSTEM_PROMPT = """You are an expert browser operator. You drive a real browser on a banking demo site. You see it only as a screenshot.

## What you see
Every look shows a screenshot with red numbered boxes, plus a text list like [7] 'Transfer'. Only text gets a number. Empty input boxes and icons have none: point at them by x,y on the screenshot. Numbers change after every look; use only the latest ones.

## Tools
- observe: take a new look.
- click(ref), or click(x, y) for something with no number.
- type_text(text, ref or x,y), select_option(option, ref or x,y).
- type_secret(name, ref or x,y): type a stored secret ('username' or 'password'). You never see the value.
- scroll(direction), open_path(path).
- extract_value(ref, save_as, value_type, description): save a value the goal asks for. Copy nothing by hand.
- finish_business_outcome(outcome, proof_text): report the business result.
- request_missing_values(fields): every field the goal gives no value for on this page (boxes AND dropdowns) in ONE go, as [{"x":..,"y":..,"hint":..,"dropdown":true|false}]. Point at the box itself. A human answers in the control window; our code types them in; then you click submit.
- ask_human(question): whenever you are unsure. If you keep failing or a tool says STUCK, the system asks a human by itself.

## How to work
1. Call observe first. Login is exactly 3 calls, no observe in between:
   type_secret('username', x, y) -> type_secret('password', x, y) -> click the 'Log In' number.
   Aim at the empty box that belongs to each label. On a side-panel form the box is BELOW its
   label (same x as the label's left edge + 60, y = label bottom + 15); on a wide form it is to
   the RIGHT (x = label right edge + 100, same y). If a tool says NOTHING TYPED, try the other
   placement once. Never ask a human for credentials; the stored ones are correct.
2. Do the task by the shortest path. Never invent, substitute or guess a value, and never pick
   one yourself. If you are unsure or uncertain about ANYTHING (a value, which option, which
   page, what the goal means), call ask_human at once. A human can answer, take over, or stop.
3. A dropdown always shows a default option; that is NOT a choice. For every dropdown the task
   uses (e.g. from/to account), call select_option: with the goal's option, or option="" if
   the goal does not name one, so a human picks. Never accept a default silently.
   Use ONLY values the user gave you. If values are missing: FIRST open the page where the task is
   done, THEN call request_missing_values ONCE, listing every box AND every dropdown the goal gives
   no value for, even a dropdown that already shows something.
4. If a tool says a human entered a value, do not type it again.
5. Move around and fill in values yourself; no approval is needed for that. If a result says DECLINED, never retry or work around it.
6. Make ONE tool call at a time. Do not click into a field before typing; the typing tools click it.
7. Stay on this site. If the human answers, follow it. If a human took over, call observe and carry on from what you see. If a result says STOPPED, stop.
8. If the page says the login failed, stop.
9. Do not use ls, read_file, write_file, edit_file, glob, grep or task.
10. Always log out before you stop. Anything the page sends (a transfer, a payment, a form)
    is held for a human's two gates: details, then send. You never approve it yourself.
    Fill every field the goal needs BEFORE you click the final button.
11. Your final message is the answer. Start it with 'STUCK:' or 'DECLINED:' when that is what happened.
"""

class NoopAnthropicPromptCachingMiddleware(AgentMiddleware):
    """Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers."""

    name = "AnthropicPromptCachingMiddleware"

    def wrap_model_call(self, request, handler):
        return handler(request)

    async def awrap_model_call(self, request, handler):
        return await handler(request)


class LatestScreenshotOnly(AgentMiddleware):
    """Old screenshots are stale (their numbers no longer work); send the model only the newest."""

    def _trim(self, request):
        seen, msgs = False, []
        for m in reversed(request.messages):
            if isinstance(m.content, list) and any(isinstance(b, dict) and b.get("type") == "image" for b in m.content):
                if seen:
                    m = m.model_copy(update={"content": [b for b in m.content if not (isinstance(b, dict) and b.get("type") == "image")]})
                seen = True
            msgs.append(m)
        return request.override(messages=msgs[::-1])

    def wrap_model_call(self, request, handler):
        return handler(self._trim(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._trim(request))


AGENT = create_deep_agent(
    model=MODEL,
    tools=TOOLS,
    system_prompt=VISUAL_SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
    middleware=[NoopAnthropicPromptCachingMiddleware(), LatestScreenshotOnly()],
)


async def run_goal(goal: str, thread_id: str | None = None) -> str:
    """New run on a fresh thread; pass an earlier thread_id to resume it with a next message."""
    global HANDOFF
    if thread_id is None:
        HANDOFF, thread_id = HandoffState(goal=goal), f"discovery-{uuid.uuid4().hex[:8]}"
        log("start", {"base_url": BASE_URL, "viewport": list(CFG.viewport), "device_scale_factor": 1},
            "run started")
    print("thread:", thread_id)
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 4 * CFG.step_budget}
    try:
        result = await AGENT.ainvoke({"messages": [{"role": "user", "content": goal}]}, config=config)
        HANDOFF.messages, HANDOFF.answer = result["messages"], result["messages"][-1].content
        if HANDOFF.answer.startswith(("STUCK", "DECLINED")):
            HANDOFF.final_shot = await snap()
        return HANDOFF.answer
    except Exception:
        HANDOFF.messages = (await AGENT.aget_state(config)).values.get("messages", [])
        HANDOFF.final_shot = await snap()
        raise
    finally:        # banking: values live only for the run. Keep the log (labels only), drop the rest
        flag_leaks(HANDOFF.log, run_values())
        HANDOFF.redact |= run_values() | {v for v in HANDOFF.saved.values() if v}   # for save_evidence only
        HANDOFF.entered, HANDOFF.given, HANDOFF.look = {}, [], None
        HANDOFF.typed_texts.clear()


print(f"agent ready | {len(TOOLS)} tools")

# %% [markdown]
# ## Save artifact
# The event log becomes a capability YAML + crops that replay loads as is (R10-R16). Steps come
# from the log; only the name and descriptions come from the model. Labels, points, crops and
# input names only: no typed, selected or secret value is ever written.

# %%
class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


Name = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]


class OcrText(Strict):          # rung 1: the target's own text
    text: str
    ordinal: int = 1


class Anchor(Strict):           # rung 2: a label, then an offset from its box centre
    label: str
    ordinal: int = 1
    offset: tuple[int, int]


class TableCell(Strict):
    row_key: str
    column: str


class Target(Strict):
    ocr_text: OcrText | None = None
    anchor: Anchor | None = None
    template: str | None = None     # rung 3: crop path, relative to the YAML
    table_cell: TableCell | None = None

    @model_validator(mode="after")
    def findable(self) -> "Target":
        if not (self.anchor or self.template or self.table_cell):
            raise ValueError("a target needs an anchor, a template or a table cell")
        return self


class Navigate(Strict):
    action: Literal["navigate"] = "navigate"
    path: str = Field(pattern=r"^/")


class Click(Strict):
    action: Literal["click"] = "click"
    target: Target


class Type(Strict):
    action: Literal["type"] = "type"
    target: Target
    value: str                       # "{{input}}" or "{{secret:name}}", never a literal


class Select(Strict):
    action: Literal["select"] = "select"
    target: Target
    option: str                      # "{{input}}"


class Scroll(Strict):
    action: Literal["scroll"] = "scroll"
    direction: Literal["up", "down"]


class Extract(Strict):
    action: Literal["extract"] = "extract"
    target: Target
    save_as: Name


Step = Annotated[Navigate | Click | Type | Select | Scroll | Extract, Field(discriminator="action")]


class Input(Strict):
    name: Name
    type: str = "string"
    description: str = ""


class Output(Strict):
    name: Name
    type: str
    description: str


class Capability(Strict):
    schema_version: Literal[2] = 2
    name: Name
    version: int = 1
    description: str
    base_url: str = Field(pattern=r"^https?://")
    viewport: tuple[int, int]
    device_scale_factor: float = 1
    inputs: list[Input] = []
    outputs: list[Output] = []
    secrets: list[Name] = []
    steps: list[Step] = Field(min_length=1)
    checkpoint: str                  # text on the final screen that proves success


class CapabilityMeta(Strict):        # R11: the only part the model writes. Loose on purpose:
    name: str                        # slugged by build_capability, so a bad name cannot fail it
    description: str
    inputs: dict[str, str] = {}      # input name -> description; unknown names are ignored
    success_text: str


# %%
FIELD_TOOLS = {"type_text", "type_secret", "select_option", "request_value"}
STEP_TOOLS = FIELD_TOOLS | {"click", "scroll", "open_path", "extract_value"}
LOGOUT_WORDS = {"log out", "logout", "sign out", "sign off"}


def without_logout(events: list[dict]) -> list[dict]:
    """C: the agent logs out to leave the site clean; that is not part of the capability. Drop
    the trailing run of scrolls and logout clicks (unless it is all there is)."""
    end = len(events)
    while end and (events[end - 1]["tool"] == "scroll" or norm(events[end - 1].get("text")) in LOGOUT_WORDS):
        end -= 1
    tail = events[end:]
    return events[:end] if end and any(ev["tool"] == "click" for ev in tail) else events


def input_name(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_") or "value"
    return slug if slug[0].isalpha() else f"f_{slug}"


def step_events(log: list[dict]) -> list[dict]:
    """R16: drop failures, keep the last success per field. Refuse a take-over."""
    if any(ev.get("recordable") is False for ev in log):
        raise ValueError("a human take-over happened: steps we cannot see. Not saved.")
    ok = [ev for ev in log if ev["tool"] in STEP_TOOLS
          and not ev["result"].startswith((*FAILED, "BLOCKED", "STOP"))]
    key = lambda ev: (urlparse(ev["url"]).path, ev.get("label") or ev["point"])  # noqa: E731
    last = {key(ev): i for i, ev in enumerate(ok) if ev["tool"] in FIELD_TOOLS}
    return without_logout([ev for i, ev in enumerate(ok) if ev["tool"] not in FIELD_TOOLS or last[key(ev)] == i])


def checkpoint(log: list[dict], fallback: str) -> str:
    """C: after a send, the page's own response proves success (the agent's proof only if it is
    part of that response). Otherwise the agent's on-screen proof, else the model's text."""
    proof = [ev["args"]["proof_text"] for ev in log if ev["tool"] == "finish_business_outcome"]
    response = next((ev["landed"] for ev in reversed(log) if ev.get("landed")), [])
    if response:
        return next((p for p in reversed(proof) if any(norm(p) in norm(t) for t in response)), response[0])
    return proof[-1] if proof else fallback


def target(ev: dict, template: str) -> Target:
    a, own = ev.get("anchor"), ev.get("own")
    return Target(ocr_text=OcrText(text=own["text"], ordinal=own["ordinal"]) if own else None,
                  anchor=Anchor(label=a["text"], ordinal=a["ordinal"], offset=ev["offset"]) if a else None,
                  template=template if ev.get("crop") else None)


def to_step(ev: dict, template: str) -> Step:
    tool, args, name = ev["tool"], ev["args"], input_name(ev.get("label") or ev["args"].get("hint", ""))
    if tool == "open_path":       # query values come from the goal, so each becomes an input
        url = urlparse("/" + args["path"].lstrip("/"))
        query = "&".join(f"{k}={{{{{input_name(k)}}}}}" for k, _ in parse_qsl(url.query))
        return Navigate(path=url.path + (f"?{query}" if query else ""))
    if tool == "scroll":
        return Scroll(direction=args["direction"])
    if tool == "extract_value":
        cell = ev.get("table")
        return Extract(save_as=args["save_as"], target=Target(table_cell=TableCell(**cell)) if cell
                       else target({**ev, "crop": None}, template))   # its crop shows the value
    if tool == "click":
        return Click(target=target(ev, template))
    if tool == "select_option" or (tool == "request_value" and ev.get("dropdown")):
        return Select(target=target(ev, template), option=f"{{{{{name}}}}}")
    value = f"{{{{secret:{args['secret_name']}}}}}" if tool == "type_secret" else f"{{{{{name}}}}}"
    return Type(target=target(ev, template), value=value)


def step_inputs(steps: list[Step]) -> list[str]:
    """The {{input}} names the steps use, in order. {{secret:x}} is not an input."""
    used = [getattr(s, "value", None) or getattr(s, "option", None) or getattr(s, "path", "") for s in steps]
    return list(dict.fromkeys(m for u in used for m in re.findall(r"\{\{(\w+)\}\}", u)))


def used_inputs(log: list[dict]) -> list[str]:
    return step_inputs([to_step(ev, "crop.png") for ev in step_events(log)])


def build_capability(log: list[dict], meta: CapabilityMeta) -> Capability:
    """Steps, inputs and secrets come from the log only. The model's text cannot fail the build."""
    start = next(ev["args"] for ev in log if ev["tool"] == "start")
    events, name = step_events(log), input_name(meta.name)
    if leaks := [i for i, ev in enumerate(events) if ev.get("leak")]:
        raise ValueError(f"steps {leaks}: a label or target text is a value typed this run. "
                         "Not saved (it would store the value). Re-run discovery.")
    steps = [to_step(ev, f"crops/{name}/s{i}.png") for i, ev in enumerate(events)]
    names = step_inputs(steps)
    return Capability(
        name=name, description=meta.description, base_url=start["base_url"],
        viewport=start["viewport"], device_scale_factor=start["device_scale_factor"],
        inputs=[Input(name=n, description=meta.inputs.get(n) or n.replace("_", " ")) for n in names],
        outputs=[Output(name=ev["args"]["save_as"], type=ev["args"]["value_type"],
                        description=ev["args"]["description"])
                 for ev in events if ev["tool"] == "extract_value"],
        secrets=list(dict.fromkeys(ev["args"]["secret_name"] for ev in events if ev["tool"] == "type_secret")),
        steps=steps, checkpoint=checkpoint(log, meta.success_text))


def crops_for(log: list[dict], cap: Capability) -> dict[str, bytes]:
    pairs = zip(step_events(log), cap.steps)
    return {s.target.template: ev["crop"] for ev, s in pairs if getattr(s, "target", None) and s.target.template}


def save_artifact(cap: Capability, crops: dict[str, bytes], out_dir: Path = Path("artifacts/visual")) -> Path:
    path = Path(out_dir) / f"{cap.name}.yaml"
    for rel, png in crops.items():
        (Path(out_dir) / rel).parent.mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / rel).write_bytes(png)
    path.write_text(yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False))
    Capability.model_validate(yaml.safe_load(path.read_text()))     # what replay will load
    return path


async def describe(goal: str, log: list[dict]) -> CapabilityMeta:
    """R11: name, description, input descriptions, success text. Labels only, no values."""
    lines = [f"{ev['tool']} {ev.get('label') or ev.get('text') or ''}" for ev in step_events(log)]
    names = used_inputs(log)
    prompt = (f"Goal: {goal}\nSteps (tool, field label):\n" + "\n".join(lines) +
              f"\nInputs a caller fills in: {', '.join(names) or 'none'}.\n"
              "Name this capability (snake_case), describe it in one sentence, give `inputs` as a map "
              "from EXACTLY those input names to a one-line description (no other keys; secrets such "
              "as the login are not inputs), and give the text that proves success. Never include "
              "a value from the goal.")
    return await MODEL.with_structured_output(CapabilityMeta).ainvoke(prompt)


# %% [markdown]
# ## Evidence
# One folder per run under `evidence/discovery/` (spec 6.3, 3.6): the goal, every event (bytes as
# file references), the take-over screenshots, the step crops, the answer and a summary. Every run
# value and secret is masked: `***` in text, a black box over its OCR text in a PNG.

# %%
ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pyproject.toml").exists())
NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?")


def _num(text: str) -> str:
    n = text.lstrip("$").replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def redactor(values: set[str]):
    """text -> text with every value masked. Numbers match however they are written
    ('100000' = '$100,000.00'); words match whole, case-insensitively ('IL' never hits 'Bill')."""
    nums = {_num(v) for v in values if NUMBER.fullmatch(v.strip())}
    words = sorted((v for v in values if len(v.strip()) > 1 and not NUMBER.fullmatch(v.strip())),
                   key=len, reverse=True)
    word_re = re.compile("|".join(rf"(?<!\w){re.escape(w.strip())}(?!\w)" for w in words), re.I) if words else None

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


def _text(content) -> str:
    return content if isinstance(content, str) else \
        " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def transcript(messages: list, redact) -> list[dict]:
    """What the agent said and which tools it called, in order. Tool results (screenshots) skipped."""
    ai = [m for m in messages if m.type == "ai"]
    return [{"i": i, "text": redact(_text(m.content)), "tools": [c["name"] for c in m.tool_calls]}
            for i, m in enumerate(ai)]


def save_evidence(out_dir: Path = ROOT / "evidence" / "discovery", capability: Path | None = None) -> Path:
    """Write this run's evidence, masked. Call after any run, successful or not."""
    redact = redactor(HANDOFF.redact | {v for v in SECRETS.values() if v})
    yml = Path(capability).read_text() if capability else ""
    if redact(yml) != yml:            # the artifact must hold names only: never copy a leak
        raise ValueError("a run value is in the artifact")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Path(out_dir) / f"{stamp}-{input_name(redact(HANDOFF.goal))[:40]}"   # the name is masked too
    run.mkdir(parents=True, exist_ok=True)
    lines, takeovers = [], []
    for i, ev in enumerate(HANDOFF.log):
        ev = dict(ev)
        if ev["tool"] == "take_over":
            n = len(takeovers)
            takeovers.append({"reason": ev["args"].get("reason", ""), "actions": ev.get("actions", [])})
            for key, part in (("shot_before", "before"), ("shot_after", "after")):
                ev[key] = _png(run / f"take_over_{n}_{part}.png", ev.get(key), redact)
        ev["crop"] = _png(run / f"step_{i}.png", ev.get("crop"), redact)
        lines.append(json.dumps(_clean(ev, redact), default=str))
    (run / "goal.txt").write_text(redact(HANDOFF.goal) + "\n")
    (run / "answer.txt").write_text(redact(HANDOFF.answer) + "\n")
    (run / "events.jsonl").write_text("\n".join(lines) + "\n")
    (run / "transcript.jsonl").write_text("".join(json.dumps(r) + "\n" for r in transcript(HANDOFF.messages, redact)))
    _png(run / "final.png", HANDOFF.final_shot, redact)
    if capability:                    # the saved artifact + its crops, paths still relative to it
        (run / "capability.yaml").write_text(yml)
        crops = Path(capability).parent / "crops" / Path(capability).stem
        if crops.is_dir():
            shutil.copytree(crops, run / "crops" / crops.name)
    head = HANDOFF.answer.split(":", 1)[0]
    summary = {"status": head if head in ("STUCK", "DECLINED") else "done" if HANDOFF.answer else "no answer",
               "events": len(HANDOFF.log), "take_over": bool(takeovers), "take_overs": takeovers,
               "capability_saved": str(capability) if capability else None}
    (run / "summary.json").write_text(json.dumps(_clean(summary, redact), indent=2) + "\n")
    return run


def _png(path: Path, png: bytes | None, redact) -> str | None:
    if not png:
        return None
    path.write_bytes(mask_png(png, redact))
    return path.name


# %% [markdown]
# ## Run
# Log in and read a balance. Approve clicks in the control tab when asked.

# %%
answer = await run_goal("Log in, open Accounts Overview, and save the first account's balance "
                        "with extract_value as 'first_balance'. Then log out.")
print(answer)
print("saved:", HANDOFF.saved, "| events:", len(HANDOFF.log))

# %%
print(path := save_artifact(cap := build_capability(HANDOFF.log, await describe(HANDOFF.goal, HANDOFF.log)),
                            crops_for(HANDOFF.log, cap)))

# %%
print(save_evidence(capability=path))

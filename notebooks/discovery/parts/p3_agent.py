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

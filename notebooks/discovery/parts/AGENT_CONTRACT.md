# Agent contract for parts p3* (shared by the parallel builders)

Pinned by the main session, 2026-09-28, so four builders can work at once. Change it only by
agreement: if you need a change, say so in your final report and do NOT change another builder's file.

## Cell order (assemble.py PARTS)
p0 → p1 → p2 → p4 → **p3_agent** → **p3c_typing** → **p3d_nav** → **p3e_extract** → p3b_agent → p5.
p4 comes before p3, so `FakeSiteLock` and `PlaywrightSurface` exist when the agent tests run.

## Style: composition. Tools are free functions over one state object.
- `p3_agent.py` (cell 16) defines `AgentState`, `FakeSurface`, `FakeControl`, and the core tools.
- Every other tool is a free `async def tool_name(st: AgentState, ...) -> str` in its own part.
- p3b later wraps them all as LangChain tools (cell 21). Tools always RETURN a string. They never
  raise for expected refusals. Refusal prefixes: `REFUSED:`, `STALE:`, `DECLINED:`, `NO CHANGE`,
  `STOP:`, `STUCK:`, `ASK_HUMAN`.

## p3_agent.py (cell 16) MUST define exactly this
```python
@dataclass
class AgentState:
    surface: Surface            # p0 Protocol
    ocr: OcrEngine              # p0 Protocol
    cfg: DiscoveryConfig
    log: EventLog               # p2
    lock: SiteLock              # p0 Protocol (FakeSiteLock in tests)
    control: ControlWindow      # p0 Protocol (FakeControl in tests)
    given_text: str             # the goal text; values not in it need a human (type_text rule)
    secrets: Mapping[str, str]  # NAME -> value, already filtered to the current origin
    counter: RefCounter = field(default_factory=RefCounter)   # p1
    look: Look | None = None    # latest screen; None before the first observe
    declined: set[str] = field(default_factory=set)           # rejected click texts ("r" remembered)
    login_failures: int = 0
    saved: dict[str, str] = field(default_factory=dict)       # extract_value results
    act_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def page(self) -> str: ...  # last path segment of surface.url, e.g. "index.htm"

async def fresh_look(st: AgentState) -> Look               # screenshot → OCR → number() → st.look
async def act(st: AgentState, fn: Callable[[], Awaitable[None]]) -> None
    # the ONLY way to touch the site: async with st.lock.during(): await fn()
def before_crop(st: AgentState, target: Element | Point) -> bytes   # p1 cut_crop, from st.look (BEFORE the action)
def hints_for(st: AgentState, target: Element | Point) -> RungHints  # text (None if text-less), anchor, table
async def gate_click(st: AgentState, text: str | None, crop: bytes) -> str | None
    # classify_click → "deny" → "REFUSED: ..."; "ask" → st.control.approve(...);
    # "reject" → add to st.declined, return "DECLINED: ..."; approved/safe → None (go ahead).
    # A text already in st.declined → "DECLINED: ..." with no second prompt.
async def observe(st: AgentState) -> str                   # returns format_elements(...) text + the gen
async def click(st: AgentState, ref: int) -> str
async def click_at(st: AgentState, x: int, y: int) -> str  # "NO CHANGE" if screens_same before/after

class FakeSurface:   # scripted screens: list[(png, ocr_items)], advances one screen per action
    def __init__(self, screens: list[tuple[bytes, list[tuple[str, Box, float]]]], url: str) -> None
    url: str; calls: list[tuple]    # e.g. ("click", x, y), ("type", text), ("press", key), ("wheel", dx, dy), ("goto", url)
    def ocr(self, png: bytes) -> list[tuple[str, Box, float]]   # pass as st.ocr: returns that screen's items
    stay: bool = False              # True → the next action does not advance (for NO CHANGE tests)

class FakeControl:   # scripted human answers; records every prompt
    def __init__(self, decisions: list[str] = (), values: list[str | None] = (), texts: list[str] = ()) -> None
    prompts: list[tuple[str, str]]  # (kind, title/label)
```
- Every action goes `before_crop` → `gate_click` (clicks only) → `act(...)` → `fresh_look` → `st.log.record(tool, args, result, EventExtras(shot_png=..., crop_png=crop, hints=hints_for(...)))`.
- `click` / `click_at` resolve with p1 `resolve_target`.

## p3c_typing.py (cell 17): `type_text`, `type_secret`
```python
async def type_text(st, value: str, ref: int | None = None, x: int | None = None, y: int | None = None) -> str
async def type_secret(st, name: str, ref: int | None = None, x: int | None = None, y: int | None = None) -> str
```

## p3d_nav.py (cell 18): `scroll`, `select_option`, `open_path`
```python
async def scroll(st, direction: Literal["up", "down"], x: int | None = None, y: int | None = None) -> str
async def select_option(st, option: str, ref: int | None = None, x: int | None = None, y: int | None = None) -> str
async def open_path(st, path: str) -> str
```

## p3e_extract.py (cell 19): `extract_value`, `finish`, `finish_business_outcome`
```python
async def extract_value(st, ref: int, save_as: str, value_type: str, description: str) -> str
async def finish(st, summary: str) -> str
async def finish_business_outcome(st, outcome: str, proof: str) -> str
```

## Rules (every builder)
- Pure visual: site access only through `st.surface` (mouse, keyboard, screenshot, goto, url).
- No ParaBank strings in tool code. Tests may use ParaBank-shaped fixtures.
- Functions ≤40 lines, files ≤500 lines, no `typing.Any`, no bare `except`.
- A secret value is never returned, logged, or put into an exception message.

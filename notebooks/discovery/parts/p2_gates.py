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


# %% BROWSER 2b: SITEMAP. Runs once, before discovery. Not found -> carry on as usual.
# The user's own two usp lines, which fetch_sitemap_urls (OFFLINE 2b) wraps with the host gate:
#     tree = sitemap_tree_for_homepage(SITE)
#     for page in tree.all_pages(): ...page.url
# Expected on ParaBank today (no /sitemap.xml): "sitemap: none found, continuing as usual".
SITE = BASE                                   # the website we are discovering (from config)
SITEMAP_URLS = await asyncio.to_thread(fetch_sitemap_urls, SITE)
SITEMAP_CONTEXT = sitemap_context(SITEMAP_URLS, globals().get("RUN_CFG", CFG))
print(f"sitemap: {len(SITEMAP_URLS)} pages found" if SITEMAP_URLS else "sitemap: none found, continuing as usual")

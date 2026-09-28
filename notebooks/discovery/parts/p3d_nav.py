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

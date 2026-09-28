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

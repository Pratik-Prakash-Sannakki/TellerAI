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

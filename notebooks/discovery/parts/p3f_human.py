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

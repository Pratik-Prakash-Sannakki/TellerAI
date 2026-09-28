# %% OFFLINE 17: typing (type_text, type_secret) by a number or a point
SELECT_ALL_KEY = "ControlOrMeta+A"   # replace whatever the box already holds


@dataclass(frozen=True)
class _TypeJob:
    """One typing action, fixed before the keys go out (crop + hints from the look BEFORE)."""
    tool: str
    args: dict[str, object]
    point: Point
    box: Box                  # where the typed text must show up on the re-read
    crop: bytes
    hints: RungHints
    human: bool = False       # a human gave the value: never shown to the model or logged
    secret: bool = False      # a named secret: masking dots only, never shown or logged


def _where(ref: int | None, x: int | None, y: int | None) -> dict[str, object]:
    return {"ref": ref} if ref is not None else {"x": x, "y": y}


def _type_target(st: AgentState, ref: int | None, x: int | None,
                 y: int | None) -> tuple[Point, Element | Point] | str:
    """The click point + the thing to crop/hint (the element for a ref, else the point)."""
    if st.look is None:
        return "REFUSED: call observe first"
    got = _stopped(st) or resolve_target(st.look, ref, x, y, st.cfg)
    if isinstance(got, str):
        return got
    el = st.look.by_ref(ref) if ref is not None else None
    return got, (el or got)


def _field_label(st: AgentState, target: Element | Point) -> str:
    """The field's name for the human: its nearest label, else its own text."""
    centre = target.box.center if isinstance(target, Element) else target
    anchor = nearest_anchor(st.look.elements, centre, st.cfg)
    if anchor:
        return anchor.label
    return target.text if isinstance(target, Element) else f"the box at ({centre.x}, {centre.y})"


def _sensitive(st: AgentState, label: str) -> bool:
    return any(w in label.casefold() for w in st.cfg.sensitive_words)


def _in_goal(st: AgentState, value: str) -> bool:
    v = " ".join(value.casefold().split())
    return bool(v) and v in " ".join(st.given_text.casefold().split())


def _scrub_box(st: AgentState, box: Box) -> None:
    """Drop every OCR element inside the typed box from the latest look (never shown on)."""
    kept = tuple(e for e in st.look.elements if not _contains(box, e.box.center))
    st.look = Look(st.look.gen, st.look.png, kept)


def _read_ok(read: str, value: str, job: _TypeJob) -> bool:
    return typed_ok(read, value, secret=True) or (not job.secret and typed_ok(read, value, False))


async def _key_in(st: AgentState, point: Point, value: str) -> None:
    async def keys() -> None:
        await st.surface.click(point.x, point.y)
        await st.surface.press(SELECT_ALL_KEY)
        await st.surface.type(value)
    await act(st, keys)


async def _reread(st: AgentState, job: _TypeJob, value: str) -> tuple[bool, bool]:
    """Poll fresh looks until the box shows the value (or leaks a secret). -> (ok, leaked)."""
    seen = {"ok": False, "leaked": False}

    async def once() -> bool:
        read = read_box_text((await fresh_look(st)).elements, job.box)
        seen["leaked"] = job.secret and secret_leaked(read, value)
        seen["ok"] = not seen["leaked"] and _read_ok(read, value, job)
        return seen["ok"] or seen["leaked"]
    await poll_until(once, st.cfg.poll_budget_ms, st.cfg.poll_ms)
    return seen["ok"], seen["leaked"]


def _verdict(st: AgentState, job: _TypeJob, ok: bool, leaked: bool) -> str:
    """The text the model gets back. Never the value: for human/secret jobs the box is scrubbed."""
    if leaked:
        _scrub_box(st, job.box)
        return ("STOP: the box shows the secret as plain text (not a masked field). Nothing was "
                "logged. A human must check this field. Do not type it again.")
    if not ok and job.secret:
        return "STOP: the box shows no masking dots after typing the secret. A human must check it."
    if not ok:
        return "NO CHANGE: typed, but the box does not show the text. Call observe and check the field."
    if job.human or job.secret:
        _scrub_box(st, job.box)
    head = "OK: a human entered the value (not shown to you)." if job.human else f"OK: {job.tool} done."
    return f"{head}\nNew screen (gen {st.look.gen}, page {st.page()}):\n{format_elements(st.look.elements)}"


async def _run_job(st: AgentState, job: _TypeJob, value: str) -> str:
    """act (click + select all + type) -> re-read -> verdict -> one log line. The value stays local."""
    shot = st.look.png
    await _key_in(st, job.point, value)
    ok, leaked = await _reread(st, job, value)
    result = _verdict(st, job, ok, leaked)
    if result.startswith("STOP"):
        await st.control.status(f"{job.tool} on page {st.page()} stopped: {result.split(': ', 1)[1]}")
    extras = EventExtras(shot_png=shot, crop_png=job.crop, hints=job.hints, human_entry=job.human)
    return _record(st, job.tool, job.args, result, extras)


async def type_text(st: AgentState, value: str, ref: int | None = None, x: int | None = None,
                    y: int | None = None) -> str:
    """Type `value` into box [ref] or at (x, y). A value not in the goal, or a sensitive field,
    goes to a human in the control window; our code types their answer (never logged)."""
    got = _type_target(st, ref, x, y)
    if isinstance(got, str):
        return _record(st, "type_text", _where(ref, x, y), got)
    point, target = got
    label = _field_label(st, target)
    crop, hints = before_crop(st, target), hints_for(st, target)
    job = _TypeJob("type_text", {"value": value, **_where(ref, x, y)}, point,
                   crop_box_for(target, st.cfg), crop, hints)
    if _in_goal(st, value) and not _sensitive(st, label):
        return await _run_job(st, job, value)
    job = dataclasses.replace(job, args={"field": label, **_where(ref, x, y)}, human=True)
    given = await st.control.ask_value(label, crop, masked=_sensitive(st, label))
    if not given:
        return _record(st, "type_text", job.args, f"DECLINED: no value was given for {label!r}.",
                       EventExtras(crop_png=crop, hints=hints, human_entry=True))
    return await _run_job(st, job, given)


async def type_secret(st: AgentState, name: str, ref: int | None = None, x: int | None = None,
                      y: int | None = None) -> str:
    """Type the secret called `name` (the model never sees the value). Only names allowed for
    this origin (st.secrets), only on an allowed host; the box must then show masking dots."""
    args = {"secret_name": name, **_where(ref, x, y)}
    if name not in st.secrets:
        return _record(st, "type_secret", args,
                       f"REFUSED: unknown secret {name!r}. Known names: {sorted(st.secrets)}")
    if not host_allowed(st.surface.url):
        return _record(st, "type_secret", args, "REFUSED: this site is not on the allowlist.")
    got = _type_target(st, ref, x, y)
    if isinstance(got, str):
        return _record(st, "type_secret", args, got)
    point, target = got
    job = _TypeJob("type_secret", args, point, crop_box_for(target, st.cfg),
                   before_crop(st, target), hints_for(st, target), secret=True)
    return await _run_job(st, job, st.secrets[name])


print("OK OFFLINE 17")


# %% OFFLINE 17t: tests for type_text / type_secret
_URL17 = "https://parabank.parasoft.com/parabank/index.htm"
_BOX17 = Box(250, 195, 450, 225)                      # the empty input box, right of its label
_PT17 = _BOX17.center


def _screen17(label: str, shown: str | None) -> Screen:
    """A label + an input box; `shown` = what the box displays (None = empty)."""
    labels = [(label, 100, 216)] + ([(shown, 260, 216)] if shown else [])
    found = [(label, 100, 200, 200, 222)] + ([(shown, 260, 200, 440, 222)] if shown else [])
    return render_screen(labels, [_BOX17]), items(*found)


def _state17(screens: list[Screen], given: str = "", values: list[str | None] = (),
             secrets: dict[str, str] | None = None) -> AgentState:
    fs = FakeSurface(list(screens), _URL17)
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3c_typing_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=CFG, log=EventLog(run), lock=FakeSiteLock(),
                      control=FakeControl(values=list(values)), given_text=given,
                      secrets=secrets if secrets is not None else {})


def _typed(st: AgentState) -> list[str]:
    return [c[1] for c in st.surface.calls if c[0] == "type"]


async def _test_17_goal_value_by_point() -> None:
    st = _state17([_screen17("Amount", None), _screen17("Amount", "500")], given="pay 500 to rent")
    await observe(st)
    before_png = st.look.png
    out = await type_text(st, "500", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK"), out
    assert st.surface.calls == [("click", _PT17.x, _PT17.y), ("press", SELECT_ALL_KEY),
                                ("type", "500")], st.surface.calls
    assert st.control.prompts == [], "a value from the goal needs no human"
    assert st.lock.windows == 1 and st.lock.open is False
    ev = _events(st)[-1]
    assert ev["tool"] == "type_text" and ev["args"]["value"] == "500" and ev["human_entry"] is False
    assert ev["hints"]["anchor"]["label"] == "Amount"
    crop = (st.log.run_dir / ev["crop"]).read_bytes()
    first = Look(1, before_png, number(_screen17("Amount", None)[1], RefCounter()))
    assert crop == cut_crop(before_png, crop_box_for(_PT17, CFG), first.elements, None), "crop BEFORE"
    assert not any("500" in t for t, _, _ in OCR(crop)), "the box is empty in the crop"


async def _test_17_by_ref() -> None:
    st = _state17([_screen17("Amount", "0.00"), _screen17("Amount", "500")], given="pay 500")
    await observe(st)
    ref = fuzzy_find(st.look.elements, "0.00").ref
    out = await type_text(st, "500", ref=ref)
    assert out.startswith("OK"), out
    assert st.surface.calls[0][0] == "click" and _typed(st) == ["500"]
    assert (await type_text(st, "500", ref=ref)).startswith("STALE"), "an old ref is refused"
    assert (await type_text(st, "500", ref=1, x=5, y=5)).startswith("REFUSED")


async def _test_17_human_value() -> None:
    st = _state17([_screen17("Phone", None), _screen17("Phone", "5550199")], given="pay rent",
                  values=["5550199"])
    await observe(st)
    out = await type_text(st, "1234567", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK") and "human" in out, out
    assert st.control.prompts == [("value", "Phone")], st.control.prompts
    assert _typed(st) == ["5550199"], "our code types the human's value"
    assert "5550199" not in out and "1234567" not in out
    ev = _events(st)[-1]
    assert ev["human_entry"] is True and ev["args"].get("field") == "Phone"
    assert_no_secret(st.log.run_dir, "5550199")
    assert_no_secret(st.log.run_dir, "1234567")


async def _test_17_human_declines() -> None:
    st = _state17([_screen17("Phone", None)], given="pay rent", values=[None])
    await observe(st)
    out = await type_text(st, "1234567", x=_PT17.x, y=_PT17.y)
    assert out.startswith("DECLINED"), out
    assert st.surface.calls == [] and st.lock.windows == 0


async def _test_17_sensitive() -> None:
    st = _state17([_screen17("SSN", None), _screen17("SSN", "•••••")], given="ssn is 123456789",
                  values=["987654321"])
    await observe(st)
    out = await type_text(st, "123456789", x=_PT17.x, y=_PT17.y)
    assert st.control.prompts == [("value", "SSN")], "a sensitive label -> human, even if in goal"
    assert _typed(st) == ["987654321"] and out.startswith("OK"), out
    assert "987654321" not in out
    assert_no_secret(st.log.run_dir, "987654321")


async def _test_17_secret_ok() -> None:
    secret = "hunter2-fake"
    st = _state17([_screen17("Password", None), _screen17("Password", "••••••")],
                  secrets={"password": secret})
    await observe(st)
    out = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert out.startswith("OK"), out
    assert _typed(st) == [secret], "the fake keyboard gets the value"
    assert secret not in out and st.control.prompts == []
    ev = _events(st)[-1]
    assert ev["args"] == {"secret_name": "password", "x": _PT17.x, "y": _PT17.y}, ev["args"]
    assert_no_secret(st.log.run_dir, secret)


async def _test_17_secret_refused() -> None:
    st = _state17([_screen17("Password", None)], secrets={"password": "hunter2-fake"})
    await observe(st)
    unknown = await type_secret(st, "api_key", x=_PT17.x, y=_PT17.y)
    assert unknown.startswith("REFUSED") and "password" in unknown, unknown
    assert "hunter2-fake" not in unknown
    st.surface.url = "https://evil.example.com/login"
    off = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert off.startswith("REFUSED"), off
    assert st.surface.calls == [] and st.lock.windows == 0


async def _test_17_secret_leak() -> None:
    secret = "hunter2-fake"
    st = _state17([_screen17("Password", None), _screen17("Password", secret)],
                  secrets={"password": secret})
    await observe(st)
    out = await type_secret(st, "password", x=_PT17.x, y=_PT17.y)
    assert out.startswith("STOP:"), out
    assert secret not in out
    assert st.control.statuses, "a human is told"
    assert all(secret not in s for s in st.control.statuses)
    assert all(secret not in e.text for e in st.look.elements), "the leaked text is dropped"
    assert_no_secret(st.log.run_dir, secret)


for _t17 in (_test_17_goal_value_by_point, _test_17_by_ref, _test_17_human_value,
             _test_17_human_declines, _test_17_sensitive, _test_17_secret_ok,
             _test_17_secret_refused, _test_17_secret_leak):
    run_sync(_t17())
print("OK OFFLINE 17t")

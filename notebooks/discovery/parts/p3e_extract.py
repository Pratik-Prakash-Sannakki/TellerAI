# %% OFFLINE 19: extract_value (OCR box -> typed, saved value; Q8 table read), finish, business outcome
from cua.recorder import VALUE_TYPES, value_matches_type

FINISH_MARKER = "FINISHED:"
_OUTCOME_RE = re.compile(r"[A-Z][A-Z0-9_]*")


def _squash_ws(s: str) -> str:
    return " ".join(s.split())


def _is_secret(st: AgentState, text: str) -> bool:
    return any(secret_leaked(text, v) for v in st.secrets.values() if v)


def _scrub_secrets(st: AgentState, text: str) -> str:
    """Replace every secret value in free text with its NAME (the value never reaches log or model)."""
    for name, value in st.secrets.items():
        if value:
            text = text.replace(value, f"[secret:{name}]")
    return text


def _is_header(els: Sequence[Element], target: Element) -> bool:
    """Visual D101: `target` is a column header if some cell below it reads as (row, target.text)."""
    below = [e for e in els if e.box.y1 >= target.box.y2 and _x_overlap(e.box, target.box)]
    return any((t := infer_table_cell(els, e.ref)) and t.column == target.text for e in below)


def _extract_refusal(st: AgentState, el: Element, value_type: str) -> str | None:
    if _is_header(st.look.elements, el):
        return (f"REFUSED: [{el.ref}] is a table column header, not a value. "
                "Pick the cell in the row you need, under that header.")
    if value_type not in VALUE_TYPES:
        return f"REFUSED: value_type must be one of {', '.join(VALUE_TYPES)}."
    if not value_matches_type(el.text, value_type):
        return f"REFUSED: the text in [{el.ref}] does not look like a {value_type}."
    return None


async def extract_value(st: AgentState, ref: int, save_as: str, value_type: str,
                        description: str) -> str:
    """Read box [ref] on the latest screen, type-check it and save it as `save_as`. Reading
    never touches the site. The log keeps the name, type and replay hints, never the value."""
    args: dict[str, object] = {"ref": ref, "save_as": save_as, "value_type": value_type,
                               "description": description}
    if st.look is None:
        return _record(st, "extract_value", args, "REFUSED: call observe first")
    el = st.look.by_ref(ref)
    if el is None:
        return _record(st, "extract_value", args, resolve_target(st.look, ref, None, None, st.cfg))
    if _is_secret(st, el.text):     # no shot, crop or hints: they would carry the secret
        return _record(st, "extract_value", args,
                       "REFUSED: that box shows a secret value. Secrets can never be extracted.")
    crop, hints = before_crop(st, el), hints_for(st, el)
    extras = EventExtras(shot_png=st.look.png, crop_png=crop, hints=hints)
    refusal = _extract_refusal(st, el, value_type)
    if refusal:
        return _record(st, "extract_value", args, refusal, extras)
    st.saved[save_as] = el.text.strip()
    logged = f"OK: saved {save_as!r} ({value_type})."
    _record(st, "extract_value", args, logged, extras)
    return f"{logged} Value: {st.saved[save_as]}"


async def finish(st: AgentState, summary: str) -> str:
    """End the run. Start the summary with 'STUCK:' or 'DECLINED:' when that is why it ended."""
    clean = _scrub_secrets(st, summary)
    names = sorted(st.saved)
    _record(st, "finish", {"summary": clean, "saved": names}, FINISH_MARKER)
    shown = ", ".join(f"{k}={st.saved[k]}" for k in names) or "nothing"
    return f"{FINISH_MARKER} {clean} (saved: {shown}). Stop now."


async def finish_business_outcome(st: AgentState, outcome: str, proof_text: str) -> str:
    """End the run as a known business outcome (a bad-input probe). `proof_text` must be on the
    CURRENT screen: it is checked against the joined OCR text, whitespace-normalised."""
    proof = _squash_ws(proof_text)
    args: dict[str, object] = {"outcome": outcome, "proof_text": proof}
    look = await fresh_look(st)
    if not _OUTCOME_RE.fullmatch(outcome):
        result = "REFUSED: outcome must be a short UPPER_SNAKE name, e.g. ACCOUNT_NOT_FOUND."
    elif not proof or _is_secret(st, proof) or proof not in _squash_ws(look.text()):
        result = "REFUSED: that exact text is not on the current screen. Copy it exactly from the screen."
    else:
        extras = EventExtras(shot_png=look.png, extra={"outcome": outcome, "proof": proof})
        _record(st, "finish_business_outcome", args, FINISH_MARKER, extras)
        return f"{FINISH_MARKER} business outcome {outcome} recorded. Stop now."
    return _record(st, "finish_business_outcome", {"outcome": outcome}, result)


print("OK OFFLINE 19")


# %% OFFLINE 19t: tests for extract_value, finish, finish_business_outcome
_URL19 = "https://parabank.parasoft.com/parabank/overview.htm"
_ACC19 = load_ocr_fixture("accounts")
_LONE19 = items(("Balance", 100, 200, 170, 220), ("$100.00", 200, 200, 270, 220))
_ERR19 = items(("Error!", 100, 100, 160, 120), ("Could not find", 100, 150, 220, 170),
               ("account #99999.", 230, 150, 360, 170))


def _state19(found: list, secrets: dict[str, str] | None = None) -> AgentState:
    fs = FakeSurface([(render_screen([("screen", 100, 100)]), list(found))], _URL19)
    run = pathlib.Path(tempfile.mkdtemp(prefix="p3e_extract_"))
    return AgentState(surface=fs, ocr=fs.ocr, cfg=CFG, log=EventLog(run), lock=FakeSiteLock(),
                      control=FakeControl(), given_text="read the balance of account 20002",
                      secrets=secrets or {})


def _ev19(st: AgentState) -> list[dict]:
    return [json.loads(line) for line in st.log.path.read_text().splitlines()]


def _ref19(st: AgentState, text: str, x1: int) -> int:
    return next(e.ref for e in st.look.elements if e.text == text and e.box.x1 == x1)


async def _test_19_table_read() -> None:
    st = _state19(_ACC19)
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "currency", "The balance.")
    assert out.startswith("OK") and "$100.00" in out, out
    assert st.saved == {"balance": "$100.00"}
    ev = _ev19(st)
    assert len(ev) == 1 and ev[0]["tool"] == "extract_value"
    assert ev[0]["hints"]["table"] == {"row_key": "20002", "column": "Balance"}, ev[0]["hints"]
    assert ev[0]["args"] == {"ref": _ref19(st, "$100.00", 300), "save_as": "balance",
                             "value_type": "currency", "description": "The balance."}
    assert st.surface.calls == [] and st.lock.windows == 0, "reading never touches the site"


async def _test_19_labelled_value() -> None:
    st = _state19(_LONE19)
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "$100.00", 200), "balance", "currency", "The balance.")
    assert out.startswith("OK"), out
    hints = _ev19(st)[0]["hints"]
    assert hints["table"] is None and hints["anchor"]["label"] == "Balance", hints


async def _test_19_refusals() -> None:
    st = _state19(_ACC19)
    await fresh_look(st)
    head = await extract_value(st, _ref19(st, "Balance", 300), "balance", "string", "x")
    assert head.startswith("REFUSED") and "header" in head, head
    bad = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "integer", "x")
    assert bad.startswith("REFUSED") and "integer" in bad, bad
    unknown = await extract_value(st, _ref19(st, "$100.00", 300), "balance", "money", "x")
    assert unknown.startswith("REFUSED"), unknown
    stale = await extract_value(st, 9999, "balance", "currency", "x")
    assert stale.startswith("STALE"), stale
    assert st.saved == {} and len(_ev19(st)) == 4, "every refusal is one log line, nothing saved"
    fresh = _state19(_ACC19)
    assert (await extract_value(fresh, 1, "b", "currency", "x")).startswith("REFUSED"), "no look yet"


async def _test_19_no_secret() -> None:
    st = _state19(_ACC19, secrets={"PARABANK_PASSWORD": "20013"})
    await fresh_look(st)
    out = await extract_value(st, _ref19(st, "20013", 100), "acct", "string", "x")
    assert out.startswith("REFUSED") and "20013" not in out, out
    assert st.saved == {}
    assert_no_secret(st.log.run_dir, "20013")


async def _test_19_finish() -> None:
    st = _state19(_ACC19, secrets={"PARABANK_PASSWORD": "hunter2"})
    st.saved["balance"] = "$100.00"
    out = await finish(st, "Read the balance. hunter2")
    assert out.startswith(FINISH_MARKER), out
    assert "hunter2" not in out and "[secret:PARABANK_PASSWORD]" in out, out
    ev = _ev19(st)
    assert len(ev) == 1 and ev[0]["tool"] == "finish" and ev[0]["args"]["saved"] == ["balance"]
    assert_no_secret(st.log.run_dir, "hunter2")


async def _test_19_business_outcome() -> None:
    st = _state19(_ERR19)
    await fresh_look(st)
    ok = await finish_business_outcome(st, "ACCOUNT_NOT_FOUND", "Could not find  account\n#99999.")
    assert ok.startswith(FINISH_MARKER), ok
    ev = _ev19(st)[-1]
    assert ev["args"] == {"outcome": "ACCOUNT_NOT_FOUND", "proof_text": "Could not find account #99999."}
    missing = await finish_business_outcome(st, "ACCOUNT_NOT_FOUND", "Account locked.")
    assert missing.startswith("REFUSED"), missing
    empty = await finish_business_outcome(st, "X", "   ")
    assert empty.startswith("REFUSED"), empty
    assert (await finish_business_outcome(st, "not found", "Error!")).startswith("REFUSED")
    assert len(_ev19(st)) == 4
    unseen = _state19(_ERR19)
    assert (await finish_business_outcome(unseen, "X", "Error!")).startswith(FINISH_MARKER), \
        "no look yet -> takes one first"


assert value_matches_type("$100.00", "currency") and not value_matches_type("$100.00", "integer")
run_sync(_test_19_table_read())
run_sync(_test_19_labelled_value())
run_sync(_test_19_refusals())
run_sync(_test_19_no_secret())
run_sync(_test_19_finish())
run_sync(_test_19_business_outcome())
print("OK OFFLINE 19t")

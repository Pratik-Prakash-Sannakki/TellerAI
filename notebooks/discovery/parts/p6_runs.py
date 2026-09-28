# %% [markdown]
# ## Live runs (OFFLINE 23 helpers, BROWSER 5-8)
# The BROWSER cells below are thin wiring: every piece of logic lives in OFFLINE 23 and is tested
# with fakes in OFFLINE 23t. Each run gets its own `runs/<run_id>/` folder, a fresh `AgentState`
# and a fresh agent, in the one browser opened by BROWSER 2 (site locked the whole time).

# %% OFFLINE 23: run helpers (new run dir, agent state, goal text, streaming, summary, audit)
import collections
import contextlib
import uuid

from cua.recorder import value_matches_type


def new_run(cfg: DiscoveryConfig, start_url: str, sitemap_urls: list[str],
            root: pathlib.Path = RUNS) -> tuple[str, pathlib.Path, EventLog]:
    """A fresh runs/<run_id>/ folder: run.json (M3) written first, then an empty event log."""
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    run_dir = root / run_id
    write_run_json(run_dir, cfg, start_url, run_id, len(sitemap_urls))
    return run_id, run_dir, EventLog(run_dir)


class AuditedControl:
    """Wraps the control window: every Approve / Reject is also written to the run's log as
    APPROVED / DECLINED, with whether the site was locked while the human decided (Q-A proof).
    Every other call (ask_value, status, ...) passes straight through."""

    def __init__(self, inner: ControlWindow, log: EventLog, lock: SiteLock) -> None:
        self._inner, self._log, self._lock = inner, log, lock

    async def approve(self, title: str, details: str, crop_png: bytes | None) -> Decision:
        decision = await self._inner.approve(title, details, crop_png)
        word = "APPROVED" if decision == "approve" else "DECLINED"
        locked = bool(getattr(self._lock, "locked", False))
        self._log.record("human_approval", {"title": title}, f"{word}: {title}",
                         EventExtras(extra={"site_locked": locked}))
        return decision

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def origin_secrets(url: str, resolve: Callable[[str], str] = resolve_secret) -> dict[str, str]:
    """Secret NAME -> value, only when `url` is a real page on an allowed host (never about:blank)."""
    if url == "about:blank" or not host_allowed(url):
        return {}
    return {name: resolve(name) for name in SECRETS}


def make_state(run: RunBrowser, log: EventLog, goal: str, cfg: DiscoveryConfig, ocr: OcrEngine,
               resolve: Callable[[str], str] = resolve_secret) -> AgentState:
    """One run's AgentState over the shared browser. Secrets are looked up by NAME for the current
    origin only; the control window is wrapped so approvals land in this run's log."""
    return AgentState(surface=run.surface, ocr=ocr, cfg=cfg, log=log, lock=run.lock,
                      control=AuditedControl(run.control, log, run.lock), given_text=goal,
                      secrets=origin_secrets(run.surface.url, resolve))


@dataclass(frozen=True)
class RunSetup:
    """What every live run in this session shares (keeps start_run within 6 parameters)."""
    cfg: DiscoveryConfig
    ocr: OcrEngine
    sitemap_urls: list[str]
    make_agent: Callable[[AgentState], object]   # BROWSER 5's build_langchain_agent wiring
    root: pathlib.Path = RUNS


@dataclass(frozen=True)
class LiveRun:
    run_id: str
    run_dir: pathlib.Path
    state: AgentState
    agent: object
    thread_id: str


def start_run(run: RunBrowser, goal: str, setup: RunSetup, session_dirs: list[pathlib.Path],
              resolve: Callable[[str], str] = resolve_secret) -> LiveRun:
    """New run dir + fresh AgentState + fresh agent (so no memory leaks between runs)."""
    run_id, run_dir, log = new_run(setup.cfg, run.surface.url, setup.sitemap_urls, setup.root)
    st = make_state(run, log, goal, setup.cfg, setup.ocr, resolve)
    session_dirs.append(run_dir)
    return LiveRun(run_id, run_dir, st, setup.make_agent(st), f"visual-{run_id}")


def require_filled(**values: str) -> None:
    """Refuse to start a run while a ground-truth value is still its <PLACEHOLDER> or empty."""
    bad = [k for k, v in values.items() if not v.strip() or (v.startswith("<") and v.endswith(">"))]
    if bad:
        raise ValueError(f"fill in these values at the top of the cell first: {', '.join(bad)}")


def goal_message(goal: str, sitemap_context: str) -> str:
    """The user message: the goal, plus the sitemap page list when one was found."""
    return f"{goal}\n\n{sitemap_context}" if sitemap_context else goal


def _text_of(content: object) -> str:
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content if isinstance(content, str) else ""


def _messages(chunk: object) -> list[tuple[str, object]]:
    """(node, message) pairs from one LangGraph `updates` chunk; odd shapes are skipped."""
    pairs: list[tuple[str, object]] = []
    for node, update in (chunk.items() if isinstance(chunk, dict) else ()):
        msgs = update.get("messages") if isinstance(update, dict) else None
        if isinstance(msgs, list):
            pairs.extend((node, m) for m in msgs)
    return pairs


async def stream_agent(agent: object, message: str, thread_id: str, max_steps: int,
                       out: Callable[[str], None] = print) -> str:
    """Stream one run; print each tool call and the first line of its result. Returns the agent's
    last text, or "STUCK: ..." once more than `max_steps` tool calls were made (the step cap)."""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10 * max_steps + 20}
    payload = {"messages": [{"role": "user", "content": message}]}
    steps, final = 0, ""
    stream = agent.astream(payload, config=config, stream_mode="updates")
    async with contextlib.aclosing(stream):
        async for chunk in stream:
            for node, m in _messages(chunk):
                calls = getattr(m, "tool_calls", None) or []
                for call in calls:
                    steps += 1
                    out(f"{steps:3d} -> {call.get('name')}({json.dumps(call.get('args'), default=str)})")
                if steps > max_steps:
                    return f"STUCK: step cap of {max_steps} tool calls reached."
                if node == "tools" or getattr(m, "type", "") == "tool":
                    first = _text_of(m.content).strip().splitlines()[:1]
                    out(f"      <- {getattr(m, 'name', '')}: {(first or [''])[0][:140]}")
                elif not calls:
                    final = _text_of(m.content) or final
    return final


def read_events(run_dir: pathlib.Path) -> list[dict]:
    path = run_dir / "events.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run_summary(run_dir: pathlib.Path) -> dict[str, object]:
    """Counts for one run: steps, tools used, human entries, takeovers, hints, crops, approvals."""
    ev = read_events(run_dir)
    secret = [e for e in ev if e["tool"] == "type_secret" and e["crop"]]
    approvals = [e for e in ev if e["tool"] == "human_approval"]
    return {
        "steps": len(ev),
        "tools": dict(collections.Counter(e["tool"] for e in ev)),
        "human_entry": sum(1 for e in ev if e["human_entry"]),
        "takeovers": sum(1 for e in ev if "take_over" in e["tool"] or (e["extra"] or {}).get("take_over")),
        "hints": sum(1 for e in ev if e["hints"]),
        "table_reads": sum(1 for e in ev if e["hints"] and e["hints"].get("table")),
        "crops": sum(1 for e in ev if e["crop"]),
        "approved": sum(1 for e in approvals if e["result"].startswith("APPROVED")),
        "declined": sum(1 for e in ev if e["result"].startswith("DECLINED")),
        "approval_results": [e["result"] for e in approvals],
        "approvals_locked": bool(approvals) and all((e["extra"] or {}).get("site_locked") for e in approvals),
        "secret_crops": len(secret),
        "secret_crop_paths": [e["crop"] for e in secret],
        "saved": {e["args"]["save_as"]: e["args"]["value_type"] for e in ev
                  if e["tool"] == "extract_value" and e["result"].startswith("OK")},
    }


def _audit_run_json(run_dir: pathlib.Path) -> list[str]:
    try:
        data = json.loads((run_dir / "run.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"run.json missing or not valid JSON ({type(exc).__name__})"]
    need = {"version", "run_id", "start_url", "viewport", "device_scale_factor", "zoom"}
    if not need <= set(data) or data["version"] != RUN_JSON_VERSION:
        return ["run.json does not match the version-1 format"]
    return [] if host_allowed(data["start_url"]) else ["run.json start_url is off the allowed host"]


def audit_run(run_dir: pathlib.Path, secret_values: list[str]) -> list[str]:
    """Problems with one run dir ([] = clean). A problem text names the secret by position and the
    file, never the value. Checks: no secret in any file, run.json valid, every picture exists."""
    problems = _audit_run_json(run_dir)
    for i, value in enumerate(v for v in secret_values if v):
        try:
            assert_no_secret(run_dir, value)
        except AssertionError as exc:
            problems.append(f"secret #{i + 1}: {exc}")
    for e in read_events(run_dir):
        paths = [e["shot"], e["crop"], (e["hints"] or {}).get("crop_path")]
        problems += [f"step {e['step']}: missing file {p}" for p in paths if p and not (run_dir / p).is_file()]
    return problems


def read_run_checks(summary: dict, run_dir: pathlib.Path, saved_values: dict[str, str]) -> dict[str, bool]:
    """Run 1 expectations (PLAN Task 7, BROWSER 6)."""
    saved = summary["saved"]
    return {
        "type_secret used": summary["tools"].get("type_secret", 0) >= 1,
        "currency balance saved": any(t == "currency" and value_matches_type(saved_values.get(n, ""), t)
                                      for n, t in saved.items()),
        "table read in hints": summary["table_reads"] >= 1,
        "password crop exists": any((run_dir / p).is_file() for p in summary["secret_crop_paths"]),
    }


def transfer_run_checks(summary: dict, expect: Decision, target: str,
                        site_locked_now: bool) -> dict[str, bool]:
    """Run 2 expectations (BROWSER 7): the human's decision on the `target` click is in the log
    (other approvals, e.g. Log In, don't count) and the site stayed locked throughout."""
    want = normalise(target)
    hits = [r for r in summary["approval_results"] if want in map(normalise, re.findall(r"'([^']*)'", r))]
    approved = any(r.startswith("APPROVED") for r in hits)
    got = ({f"{target!r} APPROVED in the log": approved} if expect == "approve" else
           {f"{target!r} DECLINED in the log": any(r.startswith("DECLINED") for r in hits),
            f"{target!r} never APPROVED": not approved})
    return {**got, "site locked at every approval": summary["approvals_locked"],
            "site locked now": site_locked_now}


print("OK OFFLINE 23")


# %% OFFLINE 23t: tests for the run helpers (temp run dirs, a FAKE secret, no browser, no model)
import tempfile as _tf23
from types import SimpleNamespace as _NS23

_FAKE_SECRET23 = "hunter2-fake-secret"
_URL23 = BASE + "/index.htm"


def _fake_run23(url: str = _URL23) -> _NS23:
    return _NS23(surface=FakeSurface([(b"png", [])], url), lock=_NS23(locked=True),
                 control=FakeControl(["approve", "reject"]))


def _test_23_new_run(root: pathlib.Path) -> None:
    rid, rdir, log = new_run(CFG, _URL23, ["a", "b"], root=root)
    assert rdir == root / rid and isinstance(log, EventLog) and log.run_dir == rdir
    data = json.loads((rdir / "run.json").read_text())
    assert data["run_id"] == rid and data["sitemap_pages"] == 2 and data["start_url"] == _URL23
    rid2, _, _ = new_run(CFG, _URL23, [], root=root)
    assert rid2 != rid, "every run gets its own id"


def _test_23_make_state(root: pathlib.Path) -> None:
    asked: list[str] = []
    fake_resolve = lambda name: asked.append(name) or _FAKE_SECRET23  # noqa: E731
    _, _, log = new_run(CFG, _URL23, [], root=root)
    st = make_state(_fake_run23(), log, "read a balance", CFG, lambda png: [], resolve=fake_resolve)
    assert isinstance(st, AgentState) and st.given_text == "read a balance" and st.log is log
    assert set(st.secrets) == set(SECRETS) and sorted(asked) == sorted(SECRETS), "looked up by NAME"
    off = make_state(_fake_run23("https://evil.com/x"), log, "g", CFG, lambda png: [], resolve=fake_resolve)
    assert off.secrets == {}, "no secret for an origin off the allow list"
    blank = make_state(_fake_run23("about:blank"), log, "g", CFG, lambda png: [], resolve=fake_resolve)
    assert blank.secrets == {}, "about:blank is not a real origin"


async def _test_23_audited_control(root: pathlib.Path) -> None:
    _, rdir, log = new_run(CFG, _URL23, [], root=root)
    st = make_state(_fake_run23(), log, "g", CFG, lambda png: [], resolve=lambda n: "x-fake")
    assert await st.control.approve("Click 'Transfer'?", "d", b"crop") == "approve"
    assert await st.control.approve("Click 'Transfer'?", "d", None) == "reject"
    await st.control.status("hi")  # other methods pass straight through
    ev = [json.loads(line) for line in log.path.read_text().splitlines()]
    assert [e["result"].split(":")[0] for e in ev] == ["APPROVED", "DECLINED"]
    assert all(e["tool"] == "human_approval" and e["extra"]["site_locked"] is True for e in ev)
    assert st.control.statuses == ["hi"]
    open_run = _fake_run23()
    open_run.lock = _NS23(locked=False)
    st2 = make_state(open_run, log, "g", CFG, lambda png: [], resolve=lambda n: "x-fake")
    await st2.control.approve("t", "d", None)
    assert run_summary(rdir)["approvals_locked"] is False, "an unlocked approval must show up"


def _test_23_goal_message() -> None:
    assert goal_message("Read it.", "") == "Read it."
    msg = goal_message("Read it.", "Pages listed:\n/a.htm")
    assert msg.startswith("Read it.") and msg.endswith("/a.htm") and "\n\n" in msg


def _write_events23(rdir: pathlib.Path, secret_in_log: bool) -> None:
    log = EventLog(rdir)
    log.record("observe", {}, "Screen gen 1", EventExtras(shot_png=b"\x89PNG-shot"))
    log.record("type_secret", {"secret_name": "password"}, "OK: typed",
               EventExtras(crop_png=b"\x89PNG-pw", hints=RungHints(None, Anchor("Password", 0, 150, 0), None, None)))
    table = RungHints("$100.00", None, None, TableRead("13344", "Balance"))
    log.record("extract_value", {"save_as": "balance", "value_type": "currency"}, "OK: saved 'balance' (currency).",
               EventExtras(crop_png=b"\x89PNG-bal", hints=table))
    log.record("type_text", {"field": "Phone"}, "OK", EventExtras(human_entry=True))
    log.record("human_approval", {"title": "t"}, "DECLINED: t", EventExtras(extra={"site_locked": True}))
    if secret_in_log:
        log.record("finish", {"summary": _FAKE_SECRET23}, "FINISHED:")


def _test_23_summary(root: pathlib.Path) -> None:
    _, rdir, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(rdir, secret_in_log=False)
    s = run_summary(rdir)
    assert s["steps"] == 5 and s["tools"]["type_secret"] == 1 and s["human_entry"] == 1
    assert s["takeovers"] == 0 and s["hints"] == 2 and s["table_reads"] == 1 and s["crops"] == 2
    assert s["approved"] == 0 and s["declined"] == 1 and s["secret_crops"] == 1
    assert s["saved"] == {"balance": "currency"}


def _test_23_audit(root: pathlib.Path) -> None:
    _, good, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(good, secret_in_log=False)
    assert audit_run(good, [_FAKE_SECRET23]) == []
    _, bad, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(bad, secret_in_log=True)
    (bad / "crops" / "003.png").unlink()
    problems = audit_run(bad, [_FAKE_SECRET23, ""])
    assert any("secret" in p for p in problems) and any("003.png" in p for p in problems), problems
    assert not any(_FAKE_SECRET23 in p for p in problems), "a problem message never carries the value"
    (bad / "run.json").write_text("{not json")
    assert any("run.json" in p for p in audit_run(bad, [])), "a broken run.json is reported"


def _test_23_checks(root: pathlib.Path) -> None:
    _, rdir, _ = new_run(CFG, _URL23, [], root=root)
    _write_events23(rdir, secret_in_log=False)
    s = run_summary(rdir)
    ok = read_run_checks(s, rdir, {"balance": "$100.00"})
    assert ok == {"type_secret used": True, "currency balance saved": True,
                  "table read in hints": True, "password crop exists": True}, ok
    assert not read_run_checks(s, rdir, {"balance": "n/a"})["currency balance saved"]
    log = EventLog(rdir)
    for t in ("Click 'Log In'?", "Click 'Transfer Funds'?"):
        log.record("human_approval", {"title": t}, f"APPROVED: {t}", EventExtras(extra={"site_locked": True}))
    log.record("human_approval", {"title": "Click 'Transfer'?"}, "DECLINED: Click 'Transfer'?",
               EventExtras(extra={"site_locked": True}))
    s = run_summary(rdir)
    assert transfer_run_checks(s, "reject", "Transfer", site_locked_now=True) == {
        "'Transfer' DECLINED in the log": True, "'Transfer' never APPROVED": True,
        "site locked at every approval": True, "site locked now": True}
    assert not all(transfer_run_checks(s, "approve", "Transfer", site_locked_now=True).values()), \
        "an approved 'Log In' must not count as an approved transfer"
    assert not transfer_run_checks(s, "reject", "Transfer", site_locked_now=False)["site locked now"]


def _test_23_start_run(root: pathlib.Path) -> None:
    built: list[AgentState] = []
    make_agent = lambda st: built.append(st) or "agent-for-" + st.given_text  # noqa: E731
    session: list[pathlib.Path] = []
    lr = start_run(_fake_run23(), "move $5", RunSetup(CFG, lambda png: [], [], make_agent, root),
                   session, resolve=lambda n: "x-fake")
    assert lr.agent == "agent-for-move $5" and built == [lr.state] and session == [lr.run_dir]
    assert lr.state.log.run_dir == lr.run_dir and (lr.run_dir / "run.json").is_file()
    assert lr.thread_id.startswith("visual-") and lr.run_id in lr.thread_id


def _test_23_require_filled() -> None:
    require_filled(ACCOUNT_ID="13344", AMOUNT="5.00")
    for bad in ("<YOUR ACCOUNT ID>", "", "  "):
        with contextlib.suppress(ValueError):
            require_filled(ACCOUNT_ID=bad)
            raise AssertionError(f"placeholder {bad!r} must be refused")


class _FakeAgent23:
    """TEST ONLY: yields LangGraph-style `updates` chunks (one AI tool call, then its result)."""

    def __init__(self, turns: int) -> None:
        self.turns, self.config = turns, None

    async def astream(self, payload: dict, config: dict, stream_mode: str):
        self.config = config
        for i in range(self.turns):
            call = _NS23(content="", tool_calls=[{"name": "observe", "args": {"i": i}}])
            yield {"model": {"messages": [call]}}
            yield {"tools": {"messages": [_NS23(name="observe", content=f"Screen gen {i}\n[1] 'x'", tool_calls=[])]}}
        yield {"model": {"messages": [_NS23(content=[{"type": "text", "text": "All done."}], tool_calls=[])]}}


async def _test_23_stream() -> None:
    lines: list[str] = []
    fa = _FakeAgent23(2)
    final = await stream_agent(fa, "go", "t-1", 10, out=lines.append)
    assert final == "All done." and fa.config["configurable"]["thread_id"] == "t-1"
    assert fa.config["recursion_limit"] > 10
    assert sum("observe" in ln and "->" in ln for ln in lines) == 2
    assert any("Screen gen 0" in ln and "[1]" not in ln for ln in lines), "result prefix = first line only"
    capped = await stream_agent(_FakeAgent23(5), "go", "t-2", 3, out=lines.append)
    assert capped.startswith("STUCK:"), capped


with _tf23.TemporaryDirectory() as _d23:
    _root23 = pathlib.Path(_d23)
    _test_23_new_run(_root23)
    _test_23_make_state(_root23)
    run_sync(_test_23_audited_control(_root23))
    _test_23_goal_message()
    _test_23_summary(_root23)
    _test_23_audit(_root23)
    _test_23_checks(_root23)
    _test_23_start_run(_root23)
_test_23_require_filled()
run_sync(_test_23_stream())
print("OK OFFLINE 23t")


# %% BROWSER 5: build the agent (needs BROWSER 2 + 2b; p3b's build_tools / VISUAL_SYSTEM_PROMPT / build_middleware)
import os
import tempfile

from IPython.display import Image, display

RUN_MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-5")   # model from the MODEL env var
MAX_STEPS = 40                                               # step cap per run (tool calls)
# Q-B: ParaBank's safe list lives HERE (the run cell), never in tool code. (page, OCR text) pairs.
_MENU = ("Accounts Overview", "Transfer Funds", "Find Transactions", "Log Out")
RUN_CFG = dataclasses.replace(CFG, safe_clicks=frozenset(
    {("index.htm", "Log In")} | {(p, t) for p in ("overview.htm", "transfer.htm", "activity.htm") for t in _MENU}))
RUN_OCR = make_ocr_engine()
SESSION_RUNS: list[pathlib.Path] = []                        # every run dir made this session (BROWSER 8)


def _make_agent(st: AgentState) -> object:
    return build_langchain_agent(build_tools(st), model=RUN_MODEL, system_prompt=VISUAL_SYSTEM_PROMPT,
                                 middleware=build_middleware(st))


SETUP = RunSetup(RUN_CFG, RUN_OCR, SITEMAP_URLS, _make_agent)
# A dry build (log in a throwaway dir outside runs/), only to show what the model gets.
st = make_state(RUN, EventLog(pathlib.Path(tempfile.mkdtemp(prefix="cua-dry-"))), "", RUN_CFG, RUN_OCR)
agent = _make_agent(st)
print(f"model: {RUN_MODEL} | step cap: {MAX_STEPS} | secret names: {sorted(st.secrets)}")
print("tools:", ", ".join(t.name for t in build_tools(st)))
print(f"OK BROWSER 5 (site locked: {SITE_LOCK.locked})")


# %% BROWSER 6: run 1, read a balance (log in by type_secret, table read, extract_value, log out)
ACCOUNT_ID = "<YOUR ACCOUNT ID>"   # ground truth: EDIT ME, one of your own fake ParaBank account ids
require_filled(ACCOUNT_ID=ACCOUNT_ID)

GOAL1 = (f"Log in with type_secret, read the balance of account {ACCOUNT_ID}, "
         "save it with extract_value, then log out.")
print("You: watch the control window. Approve clicks that match the goal; the site stays locked.")
await SURFACE.goto(BASE + "/index.htm")
RUN1 = start_run(RUN, GOAL1, SETUP, SESSION_RUNS)
print(f"run 1: {RUN1.run_dir}")
FINAL1 = await stream_agent(RUN1.agent, goal_message(GOAL1, SITEMAP_CONTEXT), RUN1.thread_id, MAX_STEPS)
print("\nAGENT SAID:", FINAL1)
SUMMARY1 = run_summary(RUN1.run_dir)
print(json.dumps({k: v for k, v in SUMMARY1.items() if k != "approval_results"}, indent=2))
print("saved values:", RUN1.state.saved)
for _k, _v in read_run_checks(SUMMARY1, RUN1.run_dir, RUN1.state.saved).items():
    print(f"  {'PASS' if _v else 'FAIL'}  {_k}")
print("Eye check: the password-box crop(s) below must show an EMPTY box (cut before typing).")
for _p in SUMMARY1["secret_crop_paths"]:
    display(Image((RUN1.run_dir / _p).read_bytes()))


# %% BROWSER 7: run 2, a small transfer between your own two accounts (run twice: Approve, then Reject)
FROM_ACCOUNT = "<FROM ACCOUNT ID>"   # ground truth: EDIT ME, your own fake account to send from
TO_ACCOUNT = "<TO ACCOUNT ID>"       # ground truth: EDIT ME, your own OTHER fake account
AMOUNT = "<AMOUNT, e.g. 5.00>"       # ground truth: EDIT ME, keep it small
TRANSFER_BUTTON = "Transfer"         # the risky submit button's text, as the control window shows it
require_filled(FROM_ACCOUNT=FROM_ACCOUNT, TO_ACCOUNT=TO_ACCOUNT, AMOUNT=AMOUNT)

GOAL2 = (f"Log in with type_secret, open Transfer Funds, and transfer ${AMOUNT} from account "
         f"{FROM_ACCOUNT} to account {TO_ACCOUNT}. If the transfer is declined, finish with DECLINED:. "
         "Then log out.")
RUNS2: dict[str, LiveRun] = {}
for _decision in ("approve", "reject"):
    _word = "APPROVE" if _decision == "approve" else "REJECT"
    print(f"\n==== run 2 ({_decision}) ====")
    print(f"You: Approve the ordinary steps in the control window. When it asks to click "
          f"{TRANSFER_BUTTON!r}, click {_word}. Never touch the site window.")
    await SURFACE.goto(BASE + "/index.htm")
    _lr = start_run(RUN, GOAL2, SETUP, SESSION_RUNS)
    RUNS2[_decision] = _lr
    _final = await stream_agent(_lr.agent, goal_message(GOAL2, SITEMAP_CONTEXT), _lr.thread_id, MAX_STEPS)
    print("AGENT SAID:", _final)
    _s = run_summary(_lr.run_dir)
    print("approvals:", _s["approval_results"])
    for _k, _v in transfer_run_checks(_s, _decision, TRANSFER_BUTTON, SITE_LOCK.locked).items():
        print(f"  {'PASS' if _v else 'FAIL'}  {_k}")


# %% BROWSER 8: audit every run dir from this session, show every crop, close the browser
_secret_values = list(origin_secrets(BASE + "/index.htm").values())   # kept local; never printed
for _dir in SESSION_RUNS:
    _problems = audit_run(_dir, _secret_values)
    print(f"{_dir.name}: {'CLEAN' if not _problems else 'PROBLEMS'}")
    for _p in _problems:
        print("   -", _p)
del _secret_values
print("\nEye check: no customer data (names, addresses, other accounts) may be visible in any crop.")
for _dir in SESSION_RUNS:
    for _crop in sorted((_dir / "crops").glob("*.png")):
        print(f"{_dir.name}/crops/{_crop.name}")
        display(Image(_crop.read_bytes()))
await CONTROL.status("Run finished. Closing.")
await context.close()
await pw.stop()
print("OK BROWSER 8: browser closed")

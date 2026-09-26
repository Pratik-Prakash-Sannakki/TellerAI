# Phase 4 live wiring: an async engine mirror, plus a real-browser replay notebook

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans, task-by-task. Checkbox (`- [ ]`) syntax tracks steps.
>
> Task A (the async mirror) is pure Python, added as new cells inside the existing
> `notebooks/04_replay_engine.py`. Run it with `uv run python notebooks/04_replay_engine.py` --
> every check, sync and async, runs top to bottom in one process. Task B
> (`notebooks/05_replay_live.py`) imports Playwright and needs a real browser + API key; it is
> written here but **never run** by the agent -- only a `compile()`/`ast.parse()` syntax check is
> allowed. The user runs it for real.

**Goal:** PHASE4.md's own "Known gaps" section names this exactly: `run_capability` has never
been pointed at a real page, and the `escalate` seam has never been wired to
`agent.ipynb`'s real `human_takeover`/decision-bar mechanism. Close both gaps without touching the
already-verified sync engine (11+ tests, the real cross-phase integration with Phase 3's saved
YAML) or `agent.ipynb` itself.

**Architecture:** two deliverables, kept deliberately separate because they have different risk
profiles.

1. **The async mirror** (`run_capability_async`, `AsyncReplaySurface`, `AsyncFakeSurface`) lives
   inside `04_replay_engine.py`, next to the sync engine, so the two can be read side by side. It
   is pure Python -- no `import playwright` anywhere in this half -- and is fully exercised
   offline, the same way the sync engine already is.
2. **The live wiring** (`PlaywrightReplaySurface`, the real `escalate` implementation) is a new
   notebook, `05_replay_live.py`, that copies exactly what it needs from `agent.ipynb` (named cell
   by cell, D71-style discipline) and wires it to `run_capability_async`.

**Why a mirror, not a conversion (confirmed before writing any code):** `run_capability`'s own
`ReplaySurface` Protocol is entirely sync (`def navigate`, `def resolve`, `def click`, ...), and
`04_replay_engine.py`'s 11+ tests pass against it today. `agent.ipynb`'s real browser control is
entirely `async` -- Playwright's Python API has no usable sync mode inside a Jupyter kernel, and
the kernel already runs its own asyncio event loop, so a bridge like
`asyncio.get_event_loop().run_until_complete(...)` breaks with "this event loop is already
running" the moment it is tried. Converting the existing sync engine to async would touch its
already-passing tests for no reason; adding a parallel async engine leaves them untouched and
gives Playwright a natively-async surface to implement against.

**Tech stack:** unchanged -- Python 3.12, Pydantic v2, PyYAML, jupytext, uv, Playwright (already a
project dependency per `pyproject.toml`). No new dependency added.

**Spec:** `DECISIONS.md` D9 (checkpoint), D10 (error taxonomy), D22 (Surface seam), D26
(retries), D27 (result contract), D29 (typed inputs), D32-D34 (secrets, approval enforced in
code), D38 (risk in the artifact), D50-D62 (every Phase 1 safety mechanism: the whole-page lock,
the approval decision bar, `human_takeover`'s `block_risky`/`allow_refs`/`auto_on_navigate`),
D63-D68 (the v2 schema: locators, D68's stated `label`/`labeled_value` scoping gap), D69 (login
attempt guard), D70-D76 (the recorder rebuild: `derive_target`, `DESCRIBE_JS`,
`READ_LABELED_JS`). Brief 3.3 (replay), 3.6 (human-in-the-loop), 3.7 (the Surface seam).

**Verified before writing this plan:** `04_replay_engine.py`'s existing 8 required scenarios + 3
bonus + Section 5 integration check were re-run with `uv run python notebooks/04_replay_engine.py`
on 2026-09-26 (Python 3.12, Pydantic 2.13.5) and all pass. `agent.ipynb` was read in full via
`jupytext --to py:percent` (read-only conversion, no file written back) to get its exact current
cell content -- STEP 1/2/3, `PlaywrightSurface`, `OBSERVE_JS`/`DRAW_JS`, the lock/banner/decision
JS, `human_takeover`, `needs_human`, `current_value`, `resolve_secret`. `03_recorder.py`'s
`derive_target` (OFFLINE 3) and `DESCRIBE_JS`/`READ_LABELED_JS`/`read_labeled_value` (BROWSER 8)
were read in full, since they are the existing, tested mechanism this plan reuses for live locator
matching rather than inventing a second one.

## Global constraints

- Never launch a browser, touch ParaBank, or use an API key. `notebooks/05_replay_live.py` is
  never executed -- not even a syntax-only dry run that imports Playwright. A plain
  `ast.parse()`/`compile()` check is fine and is the only check performed on that file.
- Do not modify `agent.ipynb`, `02_artifact_schema.py`/`.ipynb`, `03_recorder.py`/`.ipynb`, or
  `PHASE1.md`-`PHASE4.md`. Read-only for all of them.
- `04_replay_engine.py` may be edited (that is Task A), but every existing sync cell's behavior
  must stay identical, and the full existing offline suite must still pass unchanged after the
  edit -- confirmed by re-running the whole file, not assumed.
- Never write, print, or commit a secret. `git status --short` before every commit; `.env` must
  never appear. Only `git add` the specific files this plan touches -- the working tree already
  has unrelated pre-existing uncommitted changes (`agent.ipynb`, `03_recorder.py`/`.ipynb`,
  `.env.example`, `pyproject.toml`, `uv.lock`, `notebooks/FINDINGS.md`, the `PHASE*.md` files, two
  untracked artifact YAMLs) that are mid-flight from other work and are not this plan's concern;
  never `git add -A` or stage them.
- `.ipynb` files carry no outputs (`nbstripout` is active project-wide, via `.git/info/attributes`
  + the local filter config).
- Small commits, matching this repo's existing style (`git log --oneline` first). Every commit
  message ends with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`. No push (no
  remote).

---

## Task A: the async mirror, inside `04_replay_engine.py`

### A1. Factor two PURE helpers out of the existing sync cells first

Before adding anything new, pull the two pieces of `run_capability`'s logic that are pure decision
logic (no surface call, no escalate call) into their own named functions, so the async engine can
call the *same* function instead of a hand-copied twin that could silently drift:

- `_target_locators(target) -> [("primary", loc), ("fallback", loc)?]` -- factored out of
  `resolve_target` (Section 3). `resolve_target` is rewritten to loop over this list; log wording
  and behavior stay byte-for-byte identical (`"resolved via primary (...)"` /
  `"primary failed, resolved via fallback (...)"`).
- `_find_outcome_rule(cap, url, text) -> OutcomeRule | None` -- factored out of `_check_outcomes`
  (Section 4). `_check_outcomes` is rewritten to call it, then keep its own escalate/logger/
  `ReplayResult` construction exactly as before.

- [ ] Refactor `resolve_target` (Section 3) to use `_target_locators`.
- [ ] Refactor `_check_outcomes` (Section 4) to use `_find_outcome_rule`.
- [ ] Re-run `uv run python notebooks/04_replay_engine.py` and confirm every existing print line
      (8 scenarios, 3 bonus, Section 5 integration) is unchanged.

### A2. `AsyncReplaySurface` (Section 7, mirrors Section 2)

Same eight method names as `ReplaySurface`, every one `async def`: `navigate`, `resolve`,
`click`, `type_text`, `select_option`, `read_value`, `current_url`, `page_text`. A
`_MinimalAsyncSurface` + `isinstance` check mirrors Section 2b exactly (including the known,
unavoidable limitation that a `runtime_checkable` Protocol only checks names exist, not
coroutine-ness -- the sync `_MinimalSurface` would also satisfy this Protocol; documented, not
hidden).

- [ ] Write `AsyncReplaySurface` (Section 7) and its smoke-test cell (Section 7b).

### A3. `resolve_target_async` + the escalate-awaiting helper (Section 8)

`resolve_target_async` is `resolve_target`'s async twin, built on the SAME `_target_locators`
helper from A1, only `surface.resolve(loc)` is awaited. A new `_call_escalate(escalate, reason,
ctx)` helper calls `escalate(reason, ctx)` and, if the result is awaitable
(`inspect.isawaitable`), awaits it before returning. This is the *one* place
`run_capability_async`'s behavior genuinely differs from `run_capability`'s: `escalate` may be an
async callable. Every existing/offline sync-style fake (a plain lambda returning `None`) is
unaffected -- `None` is not awaitable, so `_call_escalate` is a no-op wrapper for every old test.
This exists because a real live implementation showing a decision bar and waiting for a human is
inherently an awaitable action, and the whole reason this mirror exists is to let that finish
before `run_capability_async` returns to its caller.

- [ ] Write `resolve_target_async` and `_call_escalate` (Section 8).
- [ ] Checks (Section 8b): `_AsyncDictSurface` mirrors `_DictSurface`; three resolve_target_async
      cases (primary resolves, fallback resolves, both miss) mirror Section 3b; two
      `_call_escalate` cases (a sync fake's return is not awaited; an async fake's return IS
      awaited before `_call_escalate` returns) are new, since the sync engine has no equivalent
      to test.

### A4. `run_capability_async` (Section 9)

Line-for-line mirror of `run_capability` (Section 4): same input validation call
(`validate_inputs`, unchanged, shared), same step loop structure, same risky-click gate checked
*before* resolving the target or clicking, same `ResolutionError`/`TransientFailure` handling
(same exception classes, not redefined), same retry bound (never retries a risky click), same
per-step `expect` check, same outcome-rule check via a new `_check_outcomes_async` (built on the
shared `_find_outcome_rule` from A1), same checkpoint check, same output-set check, same four
`ReplayResult` statuses. Every surface call gains `await`; every `escalate(...)` call becomes
`await _call_escalate(escalate, ...)`.

- [ ] Write `_check_outcomes_async` and `run_capability_async` (Section 9).
- [ ] `AsyncFakeSurface` (Section 9b): line-for-line async twin of `FakeSurface`. `click_effects`
      stay plain sync callables (they only mutate the fake's own dict state).
- [ ] Port all 8 required scenarios + 3 bonus scenarios from Section 4b, `await`ed, against
      `AsyncFakeSurface`, run via a `asyncio.run(_run_async_checks())` wrapper (a plain script
      cell, matching the notebook's existing script-cell style).
- [ ] Port Section 5's integration check (both real example YAMLs, under-limit and over-limit
      transfer cases) as `_run_async_integration()`, run via `asyncio.run(...)`.
- [ ] Add the Section 6 markdown cell (placed before Section 7, right after Section 5) stating
      plainly: this mirror exists solely because Playwright is async-only; it is not new business
      logic; any future change to `run_capability` must also be made to `run_capability_async`
      (or the shared pure logic factored out further at that time).

### A5. Verify, then regenerate the `.ipynb`

- [ ] `uv run python notebooks/04_replay_engine.py` -- every one of the original lines
      (`test 1`... `test 8`, 3x `bonus`, `INTEGRATION CHECKS PASSED`) must appear **unchanged**,
      immediately followed by the async twins (`async test 1`... `ASYNC INTEGRATION CHECKS
      PASSED`).
- [ ] `grep -n playwright notebooks/04_replay_engine.py` -- only the top markdown comment
      mentioning it, no actual import.
- [ ] `uv run jupytext --to ipynb --output notebooks/04_replay_engine.ipynb
      notebooks/04_replay_engine.py`, confirm 0 cells carry outputs or a set `execution_count`.
- [ ] Record D77 in `DECISIONS.md` (the sync/async split, the two factored pure helpers, the
      escalate-awaiting asymmetry and why it does not count as a business-logic change).
- [ ] Commit: `notebooks/04_replay_engine.py`, `notebooks/04_replay_engine.ipynb`, `DECISIONS.md`.

---

## Task B: `notebooks/05_replay_live.py` -- wiring to the real browser

Never run by the agent. Written to be run by the user, cell by cell, against a real ParaBank
session. A paired `.ipynb` is generated the same way as Task A's (`jupytext --to ipynb`), then
only `ast.parse()`-checked, never executed.

### B1. Setup cells -- copy exactly what is needed from `agent.ipynb`, named explicitly

Matching `03_recorder.py`'s own discipline (its BROWSER 1-7 cells are labelled "copied verbatim
from agent.ipynb"), each setup cell in `05_replay_live.py` states exactly which `agent.ipynb` cell
it reproduces:

- Config + secrets (`agent.ipynb` "Setup 1/4"): `BASE`, `ALLOWED_HOSTS`, `SECRETS`,
  `resolve_secret`.
- Browser launch (`agent.ipynb` "Setup 2/4"): `async_playwright`, `page`/`context`/`browser`.
- Domain guard (`agent.ipynb` "Setup 3/4"): `host_allowed`.
- The numbered scanner + `PlaywrightSurface` (`agent.ipynb` "Setup 4/4" + "STEP 1"):
  `OBSERVE_JS` (with the STEP 1 options/submit patch already applied), `DRAW_JS`, `CLEAR_JS`,
  `format_elements`, `Observation`, `PlaywrightSurface`.
- The lock/takeover/approval mechanism (`agent.ipynb` "STEP 2"): `DECISION_JS`, `LOCK_JS`,
  `UNLOCK_JS`, `BLOCK_JS`/`UNBLOCK_JS`, `RESTRICT_JS`/`UNRESTRICT_JS`, `SYNC_UI_JS`,
  `human_takeover`, `approval_info`, the one-time takeover setup block (`_takeover_ready`).
- `_unlocked`, `_click`/`_type_text` mechanics, `needs_human`, `current_value`, `current_page`,
  `START_PAGES`, `TYPED` (`agent.ipynb` "STEP 3", the tool-independent parts only -- the LLM tool
  wrappers themselves, e.g. `@tool` decorated `click`/`type_text`, are NOT copied, since replay
  has no LLM in the loop; only their underlying mechanisms are reused).
- `DESCRIBE_JS`, `READ_LABELED_JS`, `read_labeled_value`, `HEADING_JS` (`03_recorder.py` BROWSER
  8) -- the existing, tested mechanism for finding a live element's label/container/nth/duplicate
  counts and for reading "the value next to this label." Reused verbatim rather than inventing a
  second implementation, per the task's own instruction.

- [ ] Write the setup cells, each with a one-line comment naming its exact source cell.

### B2. `class PlaywrightReplaySurface` -- implements `AsyncReplaySurface` for real

- **`navigate(path)`**: `await page.goto(BASE + path)`; raises a plain exception if
  `not host_allowed(...)` first (D80 -- see below for why this is an uncaught exception, not a
  `ReplayResult`, and why that is an honestly-stated limitation rather than a fix attempted here).
- **`resolve(locator)`**: runs `OBSERVE_JS` (numbers every element, sets `data-cua-ref`), then for
  every numbered element calls `DESCRIBE_JS(ref)` to get its rich descriptor (role, name, label,
  container, nth, name/label counts, visible text). Matches the given `Locator` against these
  descriptors per strategy (D78, below): `role` on role+name (+`within`), `label` on label text,
  `text` on visible text (+`within`), `structure` on container+tag+nth, `labeled_value` via
  `READ_LABELED_JS` directly (no numbered ref -- a `LabeledValueRef(label=...)` marker is returned
  instead, since a labeled-value read was never meant to depend on page position, D46). Returns
  the first match or `None` -- a miss is never swallowed here; the engine's own
  primary-then-fallback logic and `FAILED`-with-both-locators-named behavior does its job
  unchanged.
- **`click(ref)`, `type_text(ref, value)`, `select_option(ref, value)`**: call the exact same
  underlying mechanisms `agent.ipynb`'s tool internals already use --
  `_unlocked(page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000, force=True))` and the
  `.fill(...)`/`.select_option(...)` equivalents. Not reinvented; wrapped.
- **`read_value(ref)`**: for a `LabeledValueRef`, calls `read_labeled_value(page, ref.label)`
  again (D46's own reasoning: reading is cheap and always live, never cached from `resolve`). For
  a numbered ref, reads the live form value first (mirrors `agent.ipynb`'s `current_value`);
  if empty (the element is not a form control -- the `text`-strategy extract case, e.g.
  `transfer_funds`'s confirmation heading), falls back to the element's live `innerText` (D81).
- **`current_url()`**: `page.url`. **`page_text()`**: `(await page.inner_text("body"))[:4000]`
  (same truncation `agent.ipynb`'s `page_text` tool already uses).

- [ ] Write `PlaywrightReplaySurface`, matching the method contracts above exactly.
- [ ] Record D78 (the five-strategy live matching approach) and D81 (`read_value`'s
      form-value-then-text fallback) in `DECISIONS.md`.

### B3. Wire `escalate` to the real decision bar

- `make_escalate(cap)` returns an `async def escalate(reason, ctx)` closing over the running
  `PlaywrightReplaySurface` instance and the capability. For the risky-click case (`ctx` carries
  `step_index`), it looks up `cap.steps[ctx["step_index"]]`, resolves its target (reusing
  `resolve_target_async` + the surface's own `resolve`), builds the same `{title, details}` shape
  `agent.ipynb`'s `approval_info` builds, and calls `DECISION_JS` through the surface's page --
  the identical Approve/Reject/Take-over bar `agent.ipynb`'s `click()` tool already shows.
  - **Approve**: `await surface.click(ref)` -- the click that was gated actually happens now,
    through the surface, the same call path a normal (non-risky) click would use.
  - **Reject**: no action taken. `run_capability_async` still returns its own `NEEDS_APPROVAL`
    status (the engine's business logic is unchanged, per Task A's hard rule) -- the `reason`
    field is left to say why, and the notebook's own printed output distinguishes "declined" from
    "approved and clicked" for the human reading it.
  - **Take over**: `await human_takeover(question="", auto_on_navigate=True, block_risky=False)`,
    identical to `agent.ipynb`'s own take-over-to-submit call site.
- For a hard-failure escalate call (checkpoint/outcome-rule failure), the same decision bar
  mechanism shows the failure message with no Approve option meaningful (Reject/Take-over only,
  or a simple acknowledgement) -- kept minimal since `run_capability_async` already returns
  `FAILED` regardless of what a human does here; this call exists only to make the failure visible
  in the live browser, matching `agent.ipynb`'s own "the model can ask; the tool decides" spirit.

- [ ] Write `make_escalate` and the decision-bar wiring.
- [ ] Record D79 in `DECISIONS.md`: the approve/reject/take-over mapping above, and the explicit,
      honestly-stated limitation that a `NEEDS_APPROVAL` result can, after an Approve, describe a
      state where the click has *already happened* -- because `run_capability_async`'s own status
      logic is intentionally unchanged from `run_capability`'s (D28's "hold the session open"
      design is realized by `escalate` acting directly, not by the engine resuming its own loop).

### B4. Secrets

- `secret_resolver = resolve_secret` (copied from `agent.ipynb` Setup 1/4, D32) -- passed directly
  as `run_capability_async`'s `secrets` argument. Never printed, logged, or placed in any dict
  that gets displayed; `render()` (Task A, unchanged) is the only place a secret value is ever
  substituted into a string, and that string is typed directly into the page, never echoed.

- [ ] Confirm (by reading, not running) that no cell in `05_replay_live.py` prints a
      `resolve_secret(...)` return value directly.

### B5. The "how the user tests this" block

A markdown cell at the very top states the exact cells to run in order and the goal:

1. Run the setup cells top to bottom (B1).
2. Run the `PlaywrightReplaySurface` + `make_escalate` cells (B2-B4).
3. Load `artifacts/examples/get_account_balance.yaml` via `from_yaml` (already available from
   `run_capability_async`'s own Section 1 schema load, reused via the same
   exec-cells-into-namespace technique `04_replay_engine.py` and `03_recorder.py` already use).
4. Log in first (this capability has no login step of its own -- `login_parabank` is a separate
   capability, D45) by running `agent.ipynb`'s own login flow OR navigating and typing the test
   credentials once by hand in the opened browser, then run:
   `result = await run_capability_async(bal, PlaywrightReplaySurface(page), {"account_id":
   "<YOUR REAL ACCOUNT ID>"}, resolve_secret, escalate=make_escalate(bal))`
5. **Expected output:** a `ReplayResult` with `status == "SUCCESS"` and
   `outputs == {"balance": "$<the real balance>"}`, e.g.
   `REPLAY RESULT: SUCCESS {'balance': '$1,200.00'}` -- the same shape PHASE4.md already showed
   for the file-level (non-live) proof, now produced by a real browser tab.
6. Optionally, once the user has captured a fresh artifact with `03_recorder.py`'s CAPTURE half,
   the same steps replay that file instead.

- [ ] Write this markdown cell first in the file (matching the task's explicit placement
      instruction).

### B6. Syntax check only, then commit

- [ ] `uv run python -c "import ast; ast.parse(open('notebooks/05_replay_live.py').read())"` --
      must succeed. This is the ONLY check ever run against this file.
- [ ] `uv run jupytext --to ipynb --output notebooks/05_replay_live.ipynb
      notebooks/05_replay_live.py` (a pure text-conversion step; still never executes the code).
- [ ] Update `CLAUDE.md`'s phase list with a `05_replay_live.py` line.
- [ ] `git status --short` -- confirm only the intended files are staged, no `.env`.
- [ ] Commit: `notebooks/05_replay_live.py`, `notebooks/05_replay_live.ipynb`, `DECISIONS.md`,
      `CLAUDE.md`.

---

## Design forks considered and resolved here (not escalated)

- **Does `run_capability_async` need to change its own control flow to let an approved risky
  click "continue" the same run?** No. The sync `run_capability`'s risky-click branch calls
  `escalate(...)` and unconditionally returns `NEEDS_APPROVAL` right after -- it never consults
  `escalate`'s return value, and the target is not even resolved yet at that point. Changing this
  would be a real business-logic change to the already-tested engine, which Task A's hard rule
  forbids. Instead, `escalate` itself (owned entirely by `05_replay_live.py`, not by the engine)
  performs the resolve-and-click as a side effect when the human approves. D28's original design
  ("hold the browser open in the same session, hand back so the run resumes") is realized this
  way: the session stays open and the click genuinely happens in it, but the *resumption* is
  driven by `escalate`, not by `run_capability_async` re-entering its own loop. Documented as D79.
- **Should off-allowlist navigation return a `FAILED` `ReplayResult`?** Not without a real schema
  change: today, only `ResolutionError` and `TransientFailure` are caught inside
  `run_capability`/`run_capability_async`'s step loop; every other exception propagates
  uncaught. Adding a new caught exception type for "policy blocked" would be new business logic
  in the shared engine, which is out of scope for a live-wiring task whose Task A explicitly
  forbids engine behavior changes. `PlaywrightReplaySurface.navigate` raises a plain, clearly
  named exception instead, consistent with the engine's existing (if incomplete) exception
  contract. Documented as D80, honestly, as a known gap rather than silently accepted.

## What this plan deliberately does not build

- A resumable, cross-process approval flow (D28's "(b), the scaled version" -- a later call
  re-invokes with an approval token). This plan's `escalate` holds the browser open in the same
  process for the whole wait, matching D28's chosen "(a)" exactly, same as the existing scope
  note in that decision (D25: acceptable for a single-process CLI).
- Any fix to D68's `label`/`labeled_value` scoping gap. `PlaywrightReplaySurface.resolve` matches
  a `label`/`labeled_value` locator by label text alone (no `within`), exactly matching what the
  schema and `derive_target` already do and do not support -- if two elements share a label on a
  real page, `resolve` returns whichever `DESCRIBE_JS` scan order finds first, same ambiguity the
  recorder already documents and refuses to silently paper over at record time. Not newly
  introduced here; not closed here either.

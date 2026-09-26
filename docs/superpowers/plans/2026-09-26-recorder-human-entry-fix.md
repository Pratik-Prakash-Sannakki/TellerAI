# Recorder fix: a request_value/request_missing_values handoff is now recordable

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans, task-by-task. Checkbox (`- [ ]`) syntax tracks steps.
>
> Task 1 (the pure function) and its fixtures, and every OFFLINE-cell change to `compile_run`,
> are pure Python. Run them via a temporary harness that execs only the `OFFLINE`-prefixed cells
> of `notebooks/03_recorder.py` (same technique D70/D75 already established), `uv run python`.
> The CAPTURE-half wiring (task 2) may only be checked with `ast.parse`/`compile` -- **never run**
> by this agent. No browser, no ParaBank, no API key, ever.

**Goal:** a real bill-pay discovery run filled 4 fields via `type_text`, then called
`request_missing_values` because more fields were still empty. A human filled them in by hand
during the takeover (a text field, payee "Nagarjuana", and a dropdown, account "12345"). The run
finished for real in the browser (a genuine $20 payment went through). The recorder still refused
to compile ANY capability from it, because `compile_run`'s top-level refusal
(`notebooks/03_recorder.py` ~line 458) treats every `status == "handoff"` event as an unrecoverable
gap, with no exceptions -- even though `request_value`/`request_missing_values` open a KNOWN,
specific ref (or list of refs) before handing off, and agent.ipynb's own `current_value(ref)`
(copied verbatim into this notebook) can read exactly what the human typed or chose, right after
hand-back.

**Root cause, confirmed against the actual code before this plan was written** (not assumed):
- `_refuse_bad_run` (~line 458-460): `if any(e.get("status") == "handoff" for e in events): raise`.
  Blanket, no exceptions.
- The generic `_capture` wrapper (~line 2244, this rebuild's own mechanism, D73) wraps EVERY tool
  identically: one event per call, `status = classify_status(message)`. Both
  `request_value`/`request_missing_values`'s own success messages ("A human entered the value
  for..."/"A human filled in what they chose to...") start with `"A human"`, which
  `classify_status` (~line 158) maps to `"handoff"` -- indistinguishable, at the status level, from
  `ask_human`'s own "A human took over and handed back." or a take-over click's "A human completed
  this step manually...".
- The difference that actually matters: `request_value(ref, hint)` and `request_missing_values
  (hints)` (agent.ipynb, copied verbatim into this notebook's CAPTURE half) call
  `human_takeover(..., allow_refs=[...])` with a specific, already-known list of refs --
  `request_value` passes exactly the one ref it's asking about; `request_missing_values` computes
  its list itself via `missing_field_labels(surface.last_elements, hints)` before calling
  `human_takeover`. `ask_human` and a take-over click pass no `allow_refs` at all -- by design,
  since neither one knows in advance what a human might do.
- agent.ipynb already has `current_value(ref) -> str` (copied verbatim), which reads a field's live
  value right now -- a `<select>`'s currently-selected option text, or a plain form control's
  `.value` -- working for both cases already.

**Fix, in one line:** after a `request_value`/`request_missing_values` handoff returns, re-check
`current_value(ref)` for each ref that was opened. Whatever is now non-empty is exactly what the
human typed or selected. Turn each one into a proper `type_text`-shaped or `select_option`-shaped
synthetic event (chosen by the element's own `role`: `combobox`/`select` -> `select_option`-shaped,
else `type_text`-shaped) and feed it into the SAME event log `compile_run` already reads. There is
no such specific-ref information for `ask_human` (free-form) or a take-over click (also free-form,
D56-D62) -- those keep refusing, since there is genuinely no way to know what a human did there.

**Architecture:** unchanged two-part split (D41, D70). Task 1 below is a new pure function in the
COMPILE half, tested entirely offline. Task 2 gives `request_value`/`request_missing_values` their
OWN specialized `.coroutine` wrapper in the CAPTURE half, exactly the established pattern
`extract_value`/`finish`/`finish_business_outcome` already use (D73) -- not a rewrite of either
tool's own body. Task 3 narrows `compile_run`'s refusal rule to only the two genuinely unstructured
handoff tools. Task 4 adds a reviewability `why` note. Task 5 proves D29/D44's existing checks
(leftover-literal refusal, constant reporting) are not bypassed for a human-entered value.

**Tech Stack:** unchanged -- Python 3.12, Pydantic v2, PyYAML, jupytext, uv. No new dependency.

**Spec:** `DECISIONS.md` D23/D43 ("worked and mattered"), D29/D44 (parameterisation, leftover
check), D41-D49 (superseded Phase 3 decisions, kept in spirit), D70-D76 (the current recorder
rebuild this plan patches). New decisions this plan adds: **D82-D84** (the current highest decision
number in `DECISIONS.md` as of this plan is D81, from concurrent Phase 4 work landed in this same
repo while this plan was being written -- `git log --oneline` shows `7819959`/`6432e02` after this
plan's starting point, `e4a4d57`; this plan's new decisions are numbered to continue from that,
not from an earlier snapshot). Brief 3.2 (reviewability), 3.4 (safety/parameterisation), 3.6
(a well-reasoned handoff mechanism, not a blanket one).

**Verified:** every OFFLINE cell (25 of them, up from 19) was run with `uv run python` against a
harness that execs only `OFFLINE`-prefixed cells from `notebooks/03_recorder.py`, on 2026-09-26.
Exact output lines are in the final report, not reproduced here (plan written in the usual
red/green order, before the run). The harness itself is temporary and scratchpad-only, matching
D70/D75 -- not part of the committed notebook.

## Global constraints

- Never run a browser, Playwright, or ParaBank/API-key code. `page`, `browser`, `playwright` must
  never be imported or referenced by any `OFFLINE` cell. The CAPTURE-half wiring (task 2) is
  checked with `ast.parse`/`compile` only, never executed.
- Do not modify `agent.ipynb`, `02_artifact_schema.py/.ipynb`, `04_replay_engine.py/.ipynb`,
  `05_replay_live.py/.ipynb`, or `PHASE1/2/3/4.md`. Read-only.
- Do not modify `request_value`/`request_missing_values`'s OWN bodies beyond what is needed to
  replace `.coroutine` -- their logic (the `NOT YET`/start-page guard, `_ask_for_value`,
  `missing_field_labels`) is untouched.
- `git status --short` before every commit; `.env` must never appear. Only `git add` the files
  this plan actually touches (`notebooks/03_recorder.py`/`.ipynb`, `DECISIONS.md`, `CLAUDE.md`,
  this plan file) -- other files mid-flight in the working tree from concurrent work
  (`agent.ipynb`, `04_replay_engine.py/.ipynb`, `05_replay_live.py/.ipynb`, `pyproject.toml`,
  `uv.lock`, `.env.example`, `notebooks/FINDINGS.md`, `PHASE*.md`, the example artifacts) are never
  staged by this plan.
- `.ipynb` carries no outputs (`nbstripout` is active project-wide).
- **A live, shared working directory:** another session committed Phase 4 work (D77-D81) to this
  same repo while this plan was being executed. Before every DECISIONS.md/CLAUDE.md edit, re-check
  `git log --oneline` for the current highest D-number and re-read the file fresh -- never trust an
  earlier read of these two files once other commits have landed.

---

## Task 1: a pure, offline-testable synthesis function

`synthesize_human_entries(i_start, before_url, before_heading, after_url, after_heading, entries)`
-- `entries: [{"ref": int, "el": <descriptor dict>, "value_after": str}, ...]`, one per ref that
was opened for the human. Returns event dicts, same shape `_capture`'s wrapper already produces:
`tool` is `"type_text"` or `"select_option"` (chosen by `el["role"]`: `combobox`/`select` ->
`select_option`, else `type_text`), `status: "ok"`, `human_entered: True`, and a `why` note (task
4) the compiled step should carry. An entry whose `value_after` is still empty (the human declined
to fill it) is SKIPPED, not synthesized, and does not consume an `i`. Pure: no browser, no
network, no page access -- everything it needs is already in `entries`.

Lives in a new cell, `OFFLINE 4c` (with its checks in `OFFLINE 4d`), right after the updated
clean-up cell (`OFFLINE 4`/`4b`) and before `OFFLINE 5` (`build_steps`, which needs the
`HUMAN_ENTRY_WHY` constant this cell defines, for task 4).

**Fixtures (OFFLINE 4d), covering exactly what the task calls for:**
- One text field -> one `type_text`-shaped event.
- One dropdown -> one `select_option`-shaped event.
- Two of each in one call -> four events, in the same order as `entries`, `i` sequential.
- An entry whose value is still empty after handoff -> skipped entirely, not synthesized.
- `i` numbering: confirmed to continue correctly from `i_start`, including across a skipped entry
  in the middle of the list (no gap, no reuse of a number).

## Task 2: wire it into the real CAPTURE wrapper (browser-facing, never run)

`request_value` and `request_missing_values` move from the generic `_capture` loop into their OWN
`.coroutine` wrapper, in a new cell `BROWSER 10b`, following the exact established pattern
`extract_value`/`finish`/`finish_business_outcome` already use: save the original coroutine, call
it unchanged, do extra work around it, return its result unchanged.

- **`request_value(ref, hint)`:** the wrapper captures `el = describe_ref(ref)` BEFORE calling the
  original (same order the generic `_capture` already uses), calls the original, then appends the
  ordinary "handoff" audit event (status from `classify_status`, for visibility that a human was
  involved -- task 3 is what stops this alone from refusing the run). If that status is `"handoff"`,
  it reads `current_value(ref)` and, via `synthesize_human_entries`, appends one more event if the
  field is now non-empty.
- **`request_missing_values(hints)`:** the wrapper recomputes the SAME ref list the tool itself
  used -- `missing_field_labels(surface.last_elements, hints)` -- called BEFORE the original runs,
  so it reads the page at the same moment the tool did, not after the human has already changed it.
  After the call, if the audit event's status is `"handoff"`, it reads `current_value(ref)` for
  every ref in that list and lets `synthesize_human_entries` build one event per now-non-empty
  ref, silently skipping any still-empty one (surfaced normally at compile time, not specially
  handled here).
- Neither tool's own body changes. The generic `_capture` loop (`BROWSER 10`) now explicitly
  excludes `{"finish", "request_value", "request_missing_values"}` from the tools it wraps.

## Task 3: `compile_run`'s refusal rule narrows to genuinely unstructured handoffs

`_refuse_bad_run` (OFFLINE 4) keeps its hard refusal for `status == "handoff"`, but ONLY when the
event's `tool` is `ask_human` or `click` (the take-over-to-submit case inside `click()`, D56-D62)
-- `UNSTRUCTURED_HANDOFF_TOOLS = {"ask_human", "click"}`. A `request_value`/`request_missing_values`
handoff event no longer refuses on its own; it is backed by the synthetic event(s) task 2 produces,
which flow through clean-up and `build_steps` exactly like any agent-typed value would. The audit
event itself is not in `ACTION_TOOLS`, so `clean_events` still drops it as "not an action" --
nothing extra is needed there.

**Tests (OFFLINE 4b, updated; OFFLINE 12b/12c, new):**
- `ask_human`'s handoff still refuses (`_refuse_bad_run`, updated message substring) -- AND a full
  `compile_run`-level fixture (new, `OFFLINE 12b`) proves the same end to end.
- A take-over click's handoff also refuses (new case, not in the original test).
- `request_value`/`request_missing_values` handoffs do NOT refuse at `_refuse_bad_run` (new,
  direct proof).
- A full bill-pay-shaped fixture (`OFFLINE 12c`) -- 4 agent-typed/clicked steps, then a
  `request_missing_values` handoff backed by two synthetic entries (one `type_text`, one
  `select_option`) -- compiles successfully, with both synthesized steps present in
  `task.steps`, each carrying the task-4 `why` note.

## Task 4: reviewability -- a `why` note for a human-entered step

`build_steps` (OFFLINE 5) sets `why=HUMAN_ENTRY_WHY` on the compiled `TypeText`/`Select` step
whenever its source event has `human_entered: True` (only ever true for a `synthesize_human_entries`
output, never for the agent's own `type_text`/`select_option`). `HUMAN_ENTRY_WHY = "Value entered
by a human during discovery; the agent did not have this value."` -- the same field, and the same
kind of note, `build_steps` already writes on a risky `Click` step ("Point of no return...").

## Task 5: D29/D44 still apply, unmodified, to a human-entered value

No new code needed here -- `find_leftovers` and `_params`'s constant-reporting are blind to where
an event's value came from; they operate on the compiled `Capability`/typed value alone. The task
is to PROVE this with fixtures, not to add an exception (there must be none):

- **`OFFLINE 12d`:** a human-entered value that matches NO declared input (a "Remarks" field, "Thanks
  for your business") is reported in `report["constants"]`, exactly as an agent-typed constant
  would be.
- **`OFFLINE 12e`:** a human-entered value that DOES match a declared input (`payee_name`,
  "Nagarjuana"), but where the spec's own `description` text also happens to contain that literal
  un-parameterized, still triggers the leftover-literal refusal (`find_leftovers`), naming the
  input and the location, never the value -- proving the human-entered path was not special-cased
  to skip this check.

---

## Event shape recap (for the two new/changed pieces)

A synthetic event, from `synthesize_human_entries`:
```
{i, tool: "type_text"|"select_option", args: {ref, text|option}, message, status: "ok",
 before: {url, heading}, after: {url, heading}, approved: False, el: <descriptor>, value: str,
 human_entered: True, why: HUMAN_ENTRY_WHY}
```
This is deliberately the SAME shape `_capture`'s generic wrapper already produces for a real
`type_text`/`select_option` call, plus two new keys (`human_entered`, `why`) that only ever appear
on a synthesized event. `build_steps` reads `el`/`value` exactly the same way regardless of where
the event came from; only the new `why` propagation (task 4) looks at `human_entered`.

---

## Tasks

- [x] T1: this plan, committed.
- [x] T2: `synthesize_human_entries` (OFFLINE 4c) + its fixtures (OFFLINE 4d). Run offline, all
      pass. Commit.
- [x] T3: `compile_run`'s narrowed refusal (`UNSTRUCTURED_HANDOFF_TOOLS`, OFFLINE 4/4b), the `why`
      annotation in `build_steps` (OFFLINE 5), and the new compile-level fixtures (`OFFLINE
      12b`-`12e`: ask_human still refuses end to end, request_missing_values compiles with
      synthetic steps + why note, constant reporting still applies, leftover refusal still
      applies). Run the FULL offline suite, confirm every prior fixture still passes unchanged
      alongside the new ones. Commit.
- [x] T4: wire `BROWSER 10b` (the two specialized wrappers) into the CAPTURE half; update the
      generic `_capture` loop's exclusion set; update the stale `BROWSER 18` error-message branch
      and the top-of-file documentation markdown to match the new refusal wording. `ast.parse` /
      `compile` only -- never run. Regenerate the paired `.ipynb` (`uv run jupytext --to ipynb`),
      `nbstripout`-clean. Commit.
- [x] T5: `DECISIONS.md` (D82-D84, continuing from the current highest number after re-checking for
      concurrent commits) and `CLAUDE.md` (Phase 3 line, one-line update). `git status --short`,
      commit.
- [ ] Stop. Report to the user with exact output lines, `git log --oneline`, and every new decision
      number with one line each.

---

## Self-review

- **3.2** (reviewability): a step compiled from a human-entered value now carries an explicit
  `why` note saying so, distinguishing it from a step the agent decided on its own. ✓
- **3.4** (parameterisation, never silently accept an unexplained literal): D29/D44's checks are
  proven, not assumed, to still apply unmodified to a human-entered value -- both the
  leftover-refusal and the constant-reporting directions. ✓
- **3.6** (a well-reasoned handoff mechanism): the refusal is now precise about WHY it refuses
  (genuinely unknown human action) rather than a blanket rule that punished a well-structured
  handoff (a known, specific field) the same as a free-form one. ✓
- Not built here, by design: any change to `ask_human`'s or a take-over click's own mechanism
  (still, correctly, unstructured and unrecordable); a live browser run (the user's job, as
  always); Phase 9 consolidation of the duplicated setup/scanner/tool cells (unrelated to this fix).

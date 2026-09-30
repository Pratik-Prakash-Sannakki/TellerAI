# Replay decisions

Questions and decisions for the pure-visual replay engine (in design, nothing built yet).
Replay walks a saved capability with plain code, no LLM. Diagram and step table:
`replay_architecture.md` in this folder. Discovery side: `../discovery/decisions.md`.

Status key: **DECIDED** = settled by an existing doc or a user rule (source given).
**PROPOSED** = recommended default, waiting for the user's review.

## Summary

| # | Question | Decision | Status |
|---|---|---|---|
| R1 | Is there an LLM at replay? | No. Plain code walks a Pydantic-validated YAML | DECIDED |
| R2 | How is a target found? | The 3 rungs: OCR text, label + offset, picture. Never raw x,y | DECIDED |
| R3 | Screen size | 1280x800, `device_scale_factor=1`, refuse otherwise | DECIDED |
| R4 | What code does replay reuse? | Discovery's screenshot/OCR/mouse/keyboard, site lock, `SELECT_AT_JS` | DECIDED |
| R5 | How is each step checked? | OCR re-read: text shown, dots for a secret, dropdown value | DECIDED |
| R6 | Sends (transactions) | Discovery's network guard: mismatch check, Gate 1, Gate 2 | DECIDED |
| R7 | What is stored? | Nothing with values. Working values wiped at run end | DECIDED |
| R8 | Human handoffs | Missing input → form; stuck → help panel. Discovery's control tab | DECIDED |
| R9 | Hosts, secrets, site code | parabank only; `.env`; site values in config only | DECIDED |
| R10 | Where does compile live? | In discovery (`## Save artifact`); replay only loads and runs | DECIDED |
| R11 | Why a compile step if `response_format` exists? | Hybrid: steps from the event log, meaning from the agent, then merged | PROPOSED |
| R12 | What each step type compiles to | See the table in R12 | PROPOSED |
| R13 | Target schema | New visual `Target` (schema_version 2), DOM locators retired | PROPOSED |
| R14 | What rung 2 needs that discovery doesn't record | Now recorded: label box, offset, ordinal, own box, viewport | DONE |
| R15 | Auto-approve at replay | Never for sends. Both gates, every time | PROPOSED |
| R16 | Dead ends and retries | Keep the last successful action per target; drop failures and take-overs | PROPOSED |
| R17 | Replay result statuses | `SUCCESS`, `BUSINESS_OUTCOME`, `DECLINED`, `STUCK`, `FAILED` | PROPOSED |
| R18 | Drift log | Rung used per step; falls to rung 2/3 flag review | DECIDED |

---

## R1: no LLM at replay — DECIDED

**Question.** Does replay think, or only follow?

**Decision (source: CLAUDE.md "Replay = plain code, no LLM").**
- Load the capability YAML, validate it with the Pydantic model, walk its steps in order.
- Substitute `{{input}}` from the caller and `{{secret:name}}` from `.env`, at the moment of use.
- No model call anywhere on the replay path. A step the code can't do goes to a human (R8).

## R2: how a target is found — DECIDED

**Question.** Discovery clicked at a point. How does replay find the same thing, with no LLM?

**Decision (source: discovery Q7b, "The 3 rungs", Q8, Q9, Q13).**
- Try the rungs in order on a live screenshot; stop at the first hit.
  - Rung 1: OCR text (fuzzy), with an optional `ordinal` ("2nd match").
  - Rung 2: nearest label + offset, e.g. "Password", then 150px right.
  - Rung 3: `cv2.matchTemplate` of the discovery crop. Threshold in config. Two near-equal best
    matches = not found.
- Text-less targets (empty boxes, icons) have rungs 2 and 3 only.
- Table values use `TableCellLocator` (row key + column header), not the rungs (Q8).
- Never raw x,y. All rungs miss → scroll down and retry (limit in config, e.g. 5) → ask a human.

## R3: screen size — DECIDED

**Decision (source: discovery Q10 + Q16 build note 2026-09-29).**
- Page at `CFG.viewport` = 1280x800, `device_scale_factor=1`, the same as discovery.
- The capability carries the viewport it was recorded at. Replay sets it before step 1.
- Refuse to run if the first screenshot is not exactly that size, or does not match the
  capability's value. No scaling.

## R4: reuse discovery's code — DECIDED

**Decision (source: discovery Base, Q12, Q16 build notes; CLAUDE.md "no notebook-only shortcuts").**
- Screenshot → RapidOCR → Playwright mouse/keyboard only. No `page.fill`, no DOM reads.
- `SiteLock` (CDP `Input.setIgnoreInputEvents`) on for the whole run; unlocked only for the
  instant of our own action.
- Typing: clear-then-type (`into_box`).
- Dropdowns: `SELECT_AT_JS` for the `<select>` under the point, and only that (exception B).
- Copied verbatim at first (as `03_recorder.py` did); one shared module comes at the port.

## R5: every step is checked — DECIDED

**Decision (source: discovery Q7b, Q12, Tools).**
- After each action, OCR on a bounded poll (about every 200ms, up to a budget in config).
- `type_text`: the box shows the value. `type_secret`: the spot changed (dots); a plain-text
  secret on screen = stop at once. `select_option`: the closed box shows the option.
- `click` / `open_path`: the step's `expect` text (the next page's text) appears.
- A failed check is never retried blindly for a secret; it goes to a human.

## R6: sends go through the network guard — DECIDED

**Decision (source: discovery Q16 build notes 2026-09-28/29).**
- Every non-GET request is held by `page.route` (`guard_send`), however it was triggered.
- First the mismatch check: every number being sent must be one the caller gave (inputs).
  Any other number opens the fill-in form, prefilled with the page's value.
- Then Gate 1 (Approve / Edit) and Gate 2 (send it?). Gate 2 reject = `DECLINED`.
- Only the login click is exempt (`CFG.login_words`, config).

## R7: nothing stored — DECIDED

**Decision (source: discovery Q16 build note "Gate 1 = Approve / Edit").**
- Logs and results hold labels, paths, rungs, and statuses, never typed or selected values.
- `extract_value` outputs are returned to the caller only; not written to any log.
- Working values (inputs, human answers, last screenshot) are wiped when the run ends
  (`finally`). Replay never saves new crops (Q7b).

## R8: human handoffs — DECIDED

**Decision (source: discovery Q16, Q21; old engine D91).**
- Missing or invalid input → one form in the control tab (masked if sensitive), before step 1.
- Stuck (all rungs + scrolls miss, a failed check) → the help panel: answer / take over / stop.
- Take over is the one time the lock lifts; Done re-locks first. Sends during a take-over still
  go through both gates.
- No `input()` prompts. A closed control tab fails closed.

## R9: hosts, secrets, site code — DECIDED

**Decision (source: CLAUDE.md Rules).**
- Only `parabank.parasoft.com`. `host_allowed` checks every navigation.
- Secrets from `.env`, typed by keyboard, never logged, never in the YAML (names only).
- The engine has no ParaBank code. Site values (base URL, login words, viewport) live in config
  and the capability.

## R10: where the compile step lives — DECIDED

**Decision.** Discovery produces the final artifact (`## Save artifact` section of
`notebooks/discovery/discovery.py`); replay only loads and runs it. No compile step in replay.
- User rule: "the artifact discovery generates should be directly consumed by replay, no edits
  should be made."
- `build_capability(log, meta)` (pure Python, R12 + R16) → `save_artifact(cap, crops, out_dir)`
  writes `artifacts/visual/<name>.yaml` + `crops/<name>/s<i>.png`, then reloads it into the model.
- The schema v2 Pydantic models (R13) live in that section: the single source. Replay imports
  or copies them verbatim.
- Saving is a separate one-line call in the `## Run` cell; `run_goal` never auto-saves.
- Options considered and dropped: B (COMPILE section in replay), C (separate recorder notebook).

## R11: why compile, if `response_format` exists? — PROPOSED

**Question (user's words).** "Deep agents can write structured output from a Pydantic model
(langchain `response_format`); why do we need a separate YAML generation step?"

**Options considered**
- A. The agent writes the whole capability via `response_format`.
- B. Code compiles the whole capability from the event log.
- C. **Hybrid.**

**Recommended: C, hybrid.**
- **Compiled from the event log (ground truth):** steps, points, crops, rung data, table cells,
  human-entry markers, secret refs.
  - The model never saw secret or human-entered values, so it can't write them in.
  - It can't emit pixel-exact label boxes or crop images.
  - `response_format` guarantees shape, not truth: a valid-looking step can be one that never ran.
- **From the agent via `response_format`:** the meaning only.
  - `name`, `description`, input names + descriptions, which typed values are inputs vs
    constants, output descriptions, success criteria (the checkpoint text).
- **Merged, then validated** against the same Pydantic model. Merge rules:
  - Each agent input must name a field label that exists in the log; else refuse.
  - An unmatched typed field stays a constant only if its value came from the goal; a
    human-entered field becomes an input named from its label (D90's rule).
  - Checkpoint text must appear in the last look's OCR text.

## R12: what each step type compiles to — PROPOSED

| Event (`tool`) | Compiled step | Target rungs | Value |
|---|---|---|---|
| `click` | `click` | 1 (own `text`) + 2 + 3; no text → 2 + 3 | none |
| `type_text` | `type` | 2 (`label`) + 3 | `{{input}}` or constant (R11) |
| `type_secret` | `type` | 2 + 3 | `{{secret:name}}` from `args.secret_name` |
| `select_option` | `select` | 1 (current option) + 2 + 3 | `{{input}}` or constant |
| `scroll` | `scroll` | none (direction, optional point) | none |
| `open_path` | `navigate` | none (path) | query values may be `{{input}}` |
| `extract_value` | `extract` | `TableCellLocator` if `table` set, else 1 + 2 | `save_as` output |
| `request_value` | `type` or `select` | 2 + 3 | `{{input}}`, name from `hint` |
| `send` | no step (marks the next click as a send; gates fire at replay) | — | — |
| `finish_business_outcome` | `checkpoint` (proof text) | — | — |
| `take_over`, `ask_human`, `stuck` | not compiled; `take_over` makes compile refuse (R16) | — | — |

- New step type `scroll` (not in the D63 schema). Recorded scrolls replay as steps (Q13).
- `expect` per step = text of the next page (from the following event's look), when it changes.

## R13: target schema — PROPOSED

**Question.** D63's `Target` holds DOM locators (role, label, text). The visual engine can't use them.

**Recommended:** `schema_version: 2`, in the replay notebook, reusing D63-D66 for everything else.
- `Target` = `ocr_text` (rung 1) | `anchor` (rung 2) | `template` (rung 3 crop path), each optional,
  at least one of rung 2/3. Plus `table_cell` for extracts.
- `anchor`: label text, label ordinal, offset `(dx, dy)` from the label box centre.
- `template`: path to a PNG in the capability's crops folder (blanked per Q14), not inline.
- `Capability` gains `viewport` and `device_scale_factor`.
- `Click.risk` / `amount_input` go: sends are gated at the network (R6), not per click.

## R14: what rung 2 needs that discovery doesn't record — DONE

**Now recorded** (additive keys on the existing `log(...)` events, via `where()`):
- `anchor`: the label's `text`, `box`, and `ordinal` (Nth element on screen with the same
  normalised text), on `click`, `type_text`, `type_secret`, `select_option`, `extract_value`
  and `request_value` (human entry). `label` = the anchor text.
- `offset`: action point − label box centre.
- `own`: the clicked element's `text`, `box`, `ordinal` (rung 1), on `click` only. The text under
  the point is never used as the anchor (in a box it could be a value).
- `request_value` now also carries its crop and a `dropdown` flag.
- A `start` event per run: `base_url`, `viewport`, `device_scale_factor`.
- Still no values: no typed, selected, human or secret value in any event or the YAML.
- The log stays in memory; `save_artifact` writes the capability, not the raw log. `expect` per
  step is not recorded yet (only the final `checkpoint`).

## R15: auto-approve at replay — PROPOSED

**Options considered:** A. Old engine: auto-approve below `auto_approve_limit` (500). B. **Never
auto-approve a send.**

**Recommended: B.**
- Every send hits the mismatch check, Gate 1 and Gate 2, at replay too (banking; user rule
  "the agent never commits one").
- Non-send steps (navigate, type, select, extract, login click) need no approval.
- Kept from the old engine: never retry a risky step (D26). A send that fails is not re-sent.

## R16: dead ends and retries at compile — PROPOSED

**Recommended:**
- Drop events whose result is a refusal or failure (`REFUSED`, `NO CHANGE`, `NOTHING TYPED`,
  `STALE`, `BLOCKED`, `TYPED ... but`).
- Per target (same label or same point on the same URL), keep only the last successful action.
- Drop `ask_human` and `stuck`; they are not actions.
- Any `recordable: false` event (a take-over) → compile refuses the whole run and says why.
  A human did steps we can't see.
- A `request_value` event (`human_entry: true`, known field) is kept as an input (R12).

## R17: replay result statuses — PROPOSED

Reuse the old `ReplayResult` shape (D27), with statuses changed to fit the gates:

| Status | When |
|---|---|
| `SUCCESS` | All steps done, checkpoint text seen, outputs returned |
| `BUSINESS_OUTCOME` | An `outcome_rule` matched (e.g. account not found) |
| `DECLINED` | A human said no at Gate 2 |
| `STUCK` | Human needed and stopped, or rejected at Gate 1 / skipped the form |
| `FAILED` | Hard failure: wrong screen size, invalid YAML, host blocked, check failed after help |

- `NEEDS_APPROVAL` is retired: approval happens live in the control tab, and a missing control
  tab fails closed as `STUCK`.
- `Failure` keeps `step_index, step_action, expected, observed`; `observed` never holds a value.
- **Error taxonomy (2026-09-29, spec 3.3).** After every step replay reads the screen (OCR) and
  checks text that newly appeared (whole words, any case) against outcome rules
  `[{text, status, meaning}]`: the capability's optional `outcomes:` YAML list, else the generic
  defaults in `CFG.outcomes` (no site words in code). Three classes:
  - **BUSINESS_OUTCOME**: a legitimate answer the caller needs (e.g. "not found", "insufficient
    funds"). Stops; `reason` = the rule's meaning.
  - **Recoverable** (`RECOVER`): the session expired, or the login form's label reappears mid-run.
    Replay re-runs the capability's own login steps ONCE per run, then retries the step
    (`result.recoveries`, a `relogin` drift row). Never after a send. A slow page is covered by the
    existing bounded waits (`CFG.check_s`, `settled_change`).
  - **FAILED** (hard): an app error page ("error", "access denied"), or a second expiry. Stops with
    `failure = {step, action, expected: "step N without '<text>'", observed: first 200 chars}`.
  `outcomes:` is read by replay only; it is popped before the schema validates, so discovery's
  schema is unchanged. P1b asked discovery to add it; this is the replay-side answer.
- **Assisted flag (2026-09-29).** `ReplayResult.human` lists every take-over as
  `{step, reason, actions}` (`actions` = page paths visited + send paths, no query, no body, no typed
  values). `[]` means unattended. The status stays meaningful: a run a human rescued that then meets
  its checkpoint is still `SUCCESS`, but `human` is non-empty, and `result.summary` prints e.g.
  `SUCCESS (human intervened at step 5)`. A calling agent must check `human`, not just `status`.
  The take-over's drift entry also holds screenshots at start and hand-back (3.6). Evidence only:
  replay never learns steps from it.

## R19: hand-back button during a take-over — DECIDED (user)

The user forgets to switch to the control tab to click Done. The hand-back is a browser-extension
toolbar button (`extensions/handback/`, Manifest V3), the same one discovery uses (Q16): no content
scripts, no host permissions, so it never touches any site. The browser launches with it
(`launch_persistent_context` + `--load-extension`). Replay talks only to the extension's service
worker (`EXT`): `setMode('YOU')` when the take-over starts, `setMode('AI')` in `finally`, and a
poll of its click count (`CFG.ext_poll_s`); a rise hands back. Every call is bounded (`CFG.ext_s`)
and swallows errors: with no extension, the take-over carries on with the fallbacks, the
control-tab Done. (An idle reminder was built and removed at the user's request: nothing
interrupts a take-over.) The user pins the icon once from the
puzzle-piece menu.

It **replaced a separate small "You are in control" window** (own context, placed top-right over
CDP). **Limit:** browser-only. For desktop targets the fallback is a small always-on-top window of
our own.

**Rejected:** a bar injected into the site page. It touches the target's DOM, which breaks the core
rule (must work on legacy sites and desktop apps, where we cannot inject UI), and OCR/rungs could
see it.

## R18: drift log — DECIDED

**Decision (source: discovery "The 3 rungs").**
- Per step: which rung matched (1, 2, 3, table, scroll+N) and how many polls the check took.
- A step that keeps falling to rung 2 or 3 flags the capability for review.
- No values in it (R7).
